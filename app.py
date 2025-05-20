from flask import Flask, render_template, request, redirect, url_for, flash
import os
from survey_analyzer import run_survey_analysis

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Configure folders
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'static/results'
PLOTS_FOLDER = 'static/results/plots'

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(PLOTS_FOLDER, exist_ok=True)

# Use environment variable for API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-key-here")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'survey_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['survey_file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        if not (file.filename.endswith('.csv') or file.filename.endswith(('.xlsx', '.xls'))):
            flash('Invalid file type. Please upload CSV or Excel file.')
            return redirect(request.url)

        try:
            filename = file.filename
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)

            result_filename = f"analyzed_{os.path.splitext(filename)[0]}.csv"
            result_path = os.path.join(RESULT_FOLDER, result_filename)

            run_survey_analysis(
                file_path=upload_path,
                openai_key=OPENAI_API_KEY,
                result_file=result_path,
                plots_folder=PLOTS_FOLDER
            )
            
            # Get list of generated plots
            plots = [f for f in os.listdir(PLOTS_FOLDER) if f.endswith('.png')]
            
            flash('Survey analysis completed successfully!')
            return redirect(url_for('results', 
                                 filename=result_filename,
                                 plots=plots))
        except Exception as e:
            flash(f"Error during analysis: {str(e)}")
            return redirect(request.url)

    return render_template('index.html')

@app.route('/results/<filename>')
def results(filename):
    result_path = os.path.join(RESULT_FOLDER, filename)
    if not os.path.exists(result_path):
        flash("Result file not found.")
        return redirect(url_for('index'))

    # Get plots from query parameter
    plots = request.args.getlist('plots')
    
    # Read analysis results
    try:
        df = pd.read_csv(result_path)
        analysis_data = df.to_dict('records')
    except Exception as e:
        analysis_data = []
        flash(f"Could not read results: {str(e)}")

    return render_template('results.html', 
                         filename=filename, 
                         plots=plots,
                         analysis_data=analysis_data)

if __name__ == '__main__':
    app.run(debug=True)