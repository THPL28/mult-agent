import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import io

logger = logging.getLogger("DataScienceAgent")

class DataScienceAgent:
    """
    Real Data Science Agent capable of handling CSV, Excel, and JSON data.
    Performs data cleaning, statistical analysis, and content generation.
    """
    
    async def analyze_dataset(self, file_path: str, file_type: str = "csv") -> Dict[str, Any]:
        """
        Loads data, detects schema, cleans missing values, and generates a robust statistical report.
        """
        logger.info(f"Analyzing {file_type} data from: {file_path}")
        
        try:
            # 1. Load Data
            df = self._load_data(file_path, file_type)
            
            # 2. Basic Cleaning
            df_clean = self._clean_data(df)
            
            # 3. Generate Statistics
            stats = self._generate_statistics(df_clean)
            
            # 4. Generate Markdown Report
            markdown_report = self._format_as_markdown(df_clean, stats, file_path)
            
            return {
                "markdown": markdown_report,
                "stats": stats,
                "row_count": len(df_clean),
                "columns": list(df_clean.columns)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
            return {"markdown": f"## ❌ Analysis Error\n\nError analyzing data: `{str(e)}`", "stats": {}}

    def _load_data(self, path: str, f_type: str) -> pd.DataFrame:
        if f_type == 'csv':
            return pd.read_csv(path)
        elif f_type in ['xlsx', 'xls', 'excel']:
            return pd.read_excel(path)
        elif f_type == 'json':
            return pd.read_json(path)
        elif f_type == 'parquet':
            return pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file type: {f_type}")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Drop empty columns
        df = df.dropna(how='all', axis=1)
        # Drop duplicates
        df = df.drop_duplicates()
        # Convert numeric columns that might be strings
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
        return df

    def _generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        stats = {
            "rows": len(df),
            "cols": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_summary": df[numeric_cols].describe().to_dict() if not numeric_cols.empty else {},
            "correlation": df[numeric_cols].corr().to_dict() if not numeric_cols.empty else {}
        }
        return stats

    def _format_as_markdown(self, df: pd.DataFrame, stats: Dict[str, Any], filename: str) -> str:
        md = f"# 📊 Data Analysis Report: {filename}\n\n"
        
        md += f"## 1. Dataset Overview\n"
        md += f"- **Rows**: {stats['rows']}\n"
        md += f"- **Columns**: {stats['cols']}\n"
        md += f"- **Memory Usage**: {df.memory_usage(deep=True).sum() / 1024:.2f} KB\n\n"

        md += "## 2. Sample Data (First 5 Rows)\n"
        md += df.head().to_markdown(index=False)
        md += "\n\n"
        
        md += "## 3. Data Quality / Missing Values\n"
        missing = {k: v for k, v in stats['missing_values'].items() if v > 0}
        if missing:
            md += "| Column | Missing Count |\n|---|---|\n"
            for col, count in missing.items():
                md += f"| {col} | {count} |\n"
        else:
            md += "✅ **No missing values detected.**\n"
        md += "\n"

        if stats['numeric_summary']:
            md += "## 4. Statistical Summary (Numeric)\n"
            # Format the describe dict table
            desc_df = pd.DataFrame(stats['numeric_summary']).T
            md += desc_df.to_markdown()
            md += "\n\n"
        
        return md

agent = DataScienceAgent()
