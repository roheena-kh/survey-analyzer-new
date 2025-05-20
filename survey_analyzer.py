from openai import OpenAI
import pandas as pd
import matplotlib.pyplot as plt
import os
import re

def load_survey(file_path):
    """Load survey data from file"""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")
    except Exception as e:
        raise ValueError(f"Error loading file: {str(e)}")

def classify_columns(df):
    """Classify columns as multiple choice or open-ended"""
    mcq_cols = []
    open_cols = []
    
    for col in df.columns:
        # Skip empty columns
        if df[col].isnull().all():
            continue
            
        # Convert to string if not already
        if df[col].dtype != 'object':
            df[col] = df[col].astype(str)
            
        # Open-ended: text columns with average length > 20
        if df[col].str.len().mean() > 20:
            open_cols.append(col)
        # MCQ: fewer than 15 unique values and not too long
        elif len(df[col].unique()) < 15 and df[col].str.len().max() < 50:
            mcq_cols.append(col)
            
    return mcq_cols, open_cols

def plot_mcqs(df, mcq_cols, plots_folder):
    """Generate plots for multiple choice questions"""
    # Clear existing plots first
    for file in os.listdir(plots_folder):
        if file.endswith('.png'):
            os.remove(os.path.join(plots_folder, file))
    
    os.makedirs(plots_folder, exist_ok=True)
    plot_files = []
    
    for col in mcq_cols:
        try:
            plt.figure(figsize=(10, 6))
            counts = df[col].value_counts()
            counts.plot(kind='bar', color='skyblue', title=f"Distribution: {col[:50]}")
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            safe_col_name = re.sub(r'[\\/*?:"<>|]', "", col)[:50]
            plot_file = f"{safe_col_name}_{int(time.time())}.png"  # Add timestamp
            plot_path = os.path.join(plots_folder, plot_file)
            
            plt.savefig(plot_path)
            plt.close()
            plot_files.append(plot_file)
        except Exception as e:
            print(f"Failed to plot {col}: {e}")
            
    return plot_files

def analyze_open_ended(df, open_cols, openai_key):
    """Analyze open-ended questions using OpenAI"""
    client = OpenAI(api_key=openai_key)
    
    for col in open_cols:
        print(f"Analyzing open-ended column: {col}")
        summaries = []
        
        for response in df[col].dropna().head(50):  # Limit to first 50 for demo
            if not str(response).strip():
                continue
                
            prompt = f"""
            Analyze this customer feedback from a bank survey:
            "{response}"

            Provide output in this format:
            - Summary: [concise summary]
            - Positive: [any positive aspects]
            - Negative: [any negative aspects]
            - Department: [relevant department to handle this]
            """
            
            try:
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Using 3.5 for cost efficiency
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3  # Less creative, more factual
                )
                summaries.append(completion.choices[0].message.content)
            except Exception as e:
                summaries.append(f"Analysis error: {str(e)}")
                
        df[f"{col}_Analysis"] = summaries
        
    return df

def run_survey_analysis(file_path, openai_key, result_file, plots_folder):
    """Main function to run survey analysis"""
    try:
        # Load and classify data
        df = load_survey(file_path)
        mcq_cols, open_cols = classify_columns(df)
        
        # Process data
        plot_files = []
        if mcq_cols:
            plot_files = plot_mcqs(df, mcq_cols, plots_folder)
            
        if open_cols:
            df = analyze_open_ended(df, open_cols, openai_key)
        
        # Save results
        df.to_csv(result_file, index=False)
        return plot_files
        
    except Exception as e:
        raise Exception(f"Survey analysis failed: {str(e)}")