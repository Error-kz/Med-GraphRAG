"""
PDF文档处理工具
使用 pdfplumber 提取PDF文件内容，生成Excel文件供后续向量化处理
"""
import logging
import pandas as pd
from tqdm import tqdm
from typing import List, Dict, Optional
from pathlib import Path
import pdfplumber
from config.settings import settings

# 配置日志
logger = logging.getLogger(__name__)


class PDFBatchProcessor:
    """
    PDF批量处理器
    用于从PDF文件中提取文本内容，生成Excel文件供后续导入到pdf_agent.db
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化PDF处理器
        
        Args:
            output_dir: 输出目录，默认使用 settings.DATA_PROCESSED_PATH
        """
        if output_dir is None:
            self.output_dir = Path(settings.DATA_PROCESSED_PATH)
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger
    
    def find_pdf_files(self, input_path: Optional[str] = None) -> List[Path]:
        """
        查找指定路径下的所有PDF文件
        
        Args:
            input_path: 输入路径，可以是文件或目录，默认使用 settings.DATA_RAW_PATH
            
        Returns:
            PDF文件路径列表
        """
        if input_path is None:
            input_path = settings.DATA_RAW_PATH
        
        path = Path(input_path)
        if path.is_file() and path.suffix.lower() == '.pdf':
            return [path]
        elif path.is_dir():
            # 递归查找所有PDF文件
            pdf_files = list(path.glob("**/*.pdf"))
            self.logger.info(f"在 {input_path} 中找到 {len(pdf_files)} 个PDF文件")
            return pdf_files
        else:
            raise ValueError(f"路径不存在或不是PDF文件: {input_path}")
    
    def extract_pdf_content(self,
                           pdf_path: Path,
                           extract_text: bool = True,
                           extract_tables: bool = False,
                           table_settings: Optional[dict] = None) -> Dict:
        """
        提取单个PDF文件的内容
        
        Args:
            pdf_path: PDF文件路径
            extract_text: 是否提取文本（默认True）
            extract_tables: 是否提取表格（默认False，当前主要用于文本提取）
            table_settings: 表格提取配置
            
        Returns:
            包含文件信息和提取内容的字典
        """
        result = {
            "file_name": pdf_path.name,
            "file_path": str(pdf_path),
            "metadata": {},
            "pages": [],
            "error": None
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 提取元数据
                result["metadata"] = pdf.metadata
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_result = {"page_number": page_num, "text": "", "tables": []}
                    
                    # 提取文本
                    if extract_text:
                        try:
                            # 使用布局模式提取文本，保留基本格式
                            text = page.extract_text(layout=False)
                            page_result["text"] = text if text else ""
                        except Exception as e:
                            self.logger.warning(f"页面 {page_num} 文本提取失败: {str(e)}")
                    
                    # 提取表格（可选）
                    if extract_tables:
                        try:
                            tables = page.extract_tables(table_settings or {})
                            if tables:
                                page_result["tables"] = tables
                        except Exception as e:
                            self.logger.warning(f"页面 {page_num} 表格提取失败: {str(e)}")
                    
                    result["pages"].append(page_result)
            
            self.logger.info(f"成功处理: {pdf_path.name} - {len(pdf.pages)} 页")
        
        except Exception as e:
            error_msg = f"处理文件失败 {pdf_path}: {str(e)}"
            result["error"] = error_msg
            self.logger.error(error_msg)
        
        return result
    
    def process_batch(self, pdf_files: List[Path],
                     save_format: str = "excel",
                     **extract_kwargs) -> pd.DataFrame:
        """
        批量处理PDF文件
        
        Args:
            pdf_files: PDF文件列表
            save_format: 保存格式，默认 "excel"（与 prepare_pdf_document 兼容）
            **extract_kwargs: 提取参数
            
        Returns:
            处理结果的DataFrame
        """
        all_results = []
        
        for i, pdf_file in tqdm(enumerate(pdf_files, 1), total=len(pdf_files), desc="处理PDF文件"):
            self.logger.info(f"处理进度: {i}/{len(pdf_files)} - {pdf_file.name}")
            result = self.extract_pdf_content(pdf_file, **extract_kwargs)
            all_results.append(result)
            
            # 每处理10个文件保存一次中间结果
            if i % 10 == 0:
                self._save_intermediate_results(all_results, f"batch_{i}")
        
        # 保存最终结果
        return self._save_results(all_results, save_format)
    
    def _save_results(self, results: List[Dict], format: str) -> pd.DataFrame:
        """
        保存处理结果
        
        Args:
            results: 处理结果列表
            format: 保存格式
            
        Returns:
            保存的DataFrame
        """
        # 生成摘要统计
        summary_data = []
        detailed_results = []
        
        for result in results:
            if result["error"]:
                summary_data.append({
                    "file_name": result["file_name"],
                    "status": "Error",
                    "error_message": result["error"],
                    "page_count": 0,
                    "text_length": 0
                })
                continue
            
            # 合并所有页面的文本
            total_text = ""
            for page in result["pages"]:
                page_text = page.get("text", "")
                if page_text:
                    total_text += page_text + "\n"
                    # 为每页创建详细记录（用于后续向量化）
                    detailed_results.append({
                        "file_name": result["file_name"],
                        "page_number": page["page_number"],
                        "text_content": page_text.strip()
                    })
            
            summary_data.append({
                "file_name": result["file_name"],
                "status": "Success",
                "error_message": "",
                "page_count": len(result["pages"]),
                "text_length": len(total_text)
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # 保存结果
        if format.lower() == "excel":
            # 保存摘要
            summary_path = self.output_dir / "pdf_extraction_summary.xlsx"
            summary_df.to_excel(summary_path, index=False)
            self.logger.info(f"摘要已保存到: {summary_path}")
            
            # 保存详细文本内容（用于导入到pdf_agent.db）
            if detailed_results:
                detailed_df = pd.DataFrame(detailed_results)
                detailed_path = self.output_dir / "pdf_detailed_text.xlsx"
                detailed_df.to_excel(detailed_path, index=False)
                self.logger.info(f"详细文本已保存到: {detailed_path} (共 {len(detailed_results)} 条记录)")
            else:
                self.logger.warning("没有提取到任何文本内容")
        
        elif format.lower() == "csv":
            summary_path = self.output_dir / "pdf_extraction_summary.csv"
            summary_df.to_csv(summary_path, index=False)
            self.logger.info(f"结果已保存到: {summary_path}")
        
        return summary_df
    
    def _save_intermediate_results(self, results: List[Dict], batch_name: str):
        """
        保存中间结果（防止处理中断丢失数据）
        
        Args:
            results: 当前处理结果
            batch_name: 批次名称
        """
        try:
            temp_df = pd.DataFrame([{
                "file_name": r["file_name"],
                "status": "Error" if r["error"] else "Success",
                "pages_processed": len(r["pages"])
            } for r in results])
            temp_df.to_csv(self.output_dir / f"progress_{batch_name}.csv", index=False)
        except Exception as e:
            self.logger.warning(f"保存中间结果失败: {str(e)}")


# 高级表格提取配置（可选，当前主要用于文本提取）
ADVANCED_TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 4,
    "join_tolerance": 10,
    "edge_min_length": 3,
    "min_words_vertical": 2,
    "min_words_horizontal": 1
}


def process_pdfs(input_path: Optional[str] = None, 
                 output_dir: Optional[str] = None,
                 extract_text: bool = True,
                 extract_tables: bool = False) -> pd.DataFrame:
    """
    处理PDF文件的便捷函数
    
    Args:
        input_path: PDF文件或目录路径，默认使用 settings.DATA_RAW_PATH
        output_dir: 输出目录，默认使用 settings.DATA_PROCESSED_PATH
        extract_text: 是否提取文本（默认True）
        extract_tables: 是否提取表格（默认False）
        
    Returns:
        处理结果的DataFrame
    """
    processor = PDFBatchProcessor(output_dir=output_dir)
    
    # 查找PDF文件
    pdf_files = processor.find_pdf_files(input_path)
    
    if not pdf_files:
        processor.logger.warning("未找到PDF文件")
        return pd.DataFrame()
    
    # 批量处理
    results_df = processor.process_batch(
        pdf_files,
        save_format="excel",
        extract_text=extract_text,
        extract_tables=extract_tables,
        table_settings=ADVANCED_TABLE_SETTINGS if extract_tables else None
    )
    
    # 打印摘要统计
    success_count = len(results_df[results_df["status"] == "Success"])
    processor.logger.info(f"处理完成: {success_count}/{len(pdf_files)} 个文件成功")
    
    if success_count > 0:
        avg_text_length = results_df[results_df["status"] == "Success"]["text_length"].mean()
        processor.logger.info(f"平均每文件: {avg_text_length:.0f} 字符")
    
    return results_df


def main():
    """主函数，用于命令行执行"""
    try:
        results_df = process_pdfs()
        if not results_df.empty:
            print("\n处理完成！")
            print(f"结果已保存到: {settings.DATA_PROCESSED_PATH}")
            print(f"详细文本文件: pdf_detailed_text.xlsx (可用于导入到pdf_agent.db)")
    except Exception as e:
        logger.error(f"处理过程发生错误: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()