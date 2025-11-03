(The file `c:\Users\vyn13\OneDrive\Desktop\Netflix_Recommendation_Engine\README.md` exists, but is empty)
# Netflix Movie Explorer

A small Streamlit app that explores movies using the TMDb API and displays a Netflix-inspired UI.

## Requirements

- Python 3.8+
- A TMDb API key (set in a `.env` file or as an environment variable named `TMDB_API_KEY`)

## Quick start (PowerShell)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Add your TMDb API key. Create a `.env` file in the project root with:

```text
TMDB_API_KEY=your_tmdb_api_key_here
```

4. Run the app:

```powershell
streamlit run app.py
```

If `streamlit` is not found, ensure the virtual environment is activated and `pip install -r requirements.txt` completed without errors.

## Notes

- The UI was adjusted to better resemble the Netflix layout (top navigation, large hero banner, thumbnail rows). Streamlit's HTML/CSS injection is used for styling; perfect pixel-identical replication isn't guaranteed, but the app aims to capture the look-and-feel.
- If you want more tuning (custom logos, background banners per movie, or horizontal scrolling carousels), tell me which area to refine and I can implement it.
