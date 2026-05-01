"""
Script to generate anonymized mockup data from real DSP records.
Used to create a shareable dataset that preserves distribution patterns without exposing PII.
"""

import pandas as pd
import random

# =============================================================================
# Configuration
# =============================================================================
# Path to the source file containing real, sensitive ONErpm data
input_path = '/Users/alecmave/Antigravity/Personal Projects/DSP Global/Data Real ONErpm.xlsx'

# Path where the generated anonymized mockup file will be saved
output_path = '/Users/alecmave/Antigravity/Personal Projects/DSP Global/analista-onerpm-dsp-main/Data_Mockup.xlsx'

# =============================================================================
# Mock Data Lists
# =============================================================================
# Fictional artist names used for anonymization
mock_artists = [
    "Nova Sky", "Lyra", "Vortex", "Ocean Whispers", "The Enigma", 
    "Solaris", "Luna Pulse", "Iron Harmony", "Ghost Rhythm", "Neon Soul",
    "Apex Hunter", "Velvet Echo", "Midnight Circuit", "Stellar Drifter", "Zenith"
]

# Fictional track/album titles used for anonymization
mock_titles = [
    "Beyond the Horizon", "Electric Heartbeat", "Shadows in the Mist", "Golden Hour", 
    "Cyber Dreams", "Liquid Fire", "Echoes of Silence", "Infinite Loop", 
    "Neon City Lights", "Silent Storm", "Prism of Light", "Temporal Shift",
    "Digital Seraph", "Lost in Space", "The Awakening"
]

def mock_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Anonymizes the input DataFrame by replacing sensitive data with mock values.
    
    Args:
        df (pd.DataFrame): The raw dataframe containing real editorial data.
        
    Returns:
        pd.DataFrame: A new dataframe with anonymized Artist, Title, UPC, and Image Links.
    """
    # Create a consistent mapping for Artists to ensure referential integrity
    unique_artists = df['Artist'].unique()
    artist_map = {artist: random.choice(mock_artists) + f" {i}" for i, artist in enumerate(unique_artists)}
    df['Artist'] = df['Artist'].map(artist_map)
    
    # Create a consistent mapping for Titles
    unique_titles = df['Title'].unique()
    title_map = {title: random.choice(mock_titles) + f" {i}" for i, title in enumerate(unique_titles)}
    df['Title'] = df['Title'].map(title_map)
    
    # Consolidate and standardize specific DSP names based on business logic requirements
    df['DSP'] = df['DSP'].replace({'Claro': 'Pandora', 'Movistar': 'Napster', 'CUACK': 'Pandora'})
    
    # Generate random 12-digit mock UPCs
    df['UPC'] = [str(random.randint(100000000000, 999999999999)) for _ in range(len(df))]
    
    # Sanitize image URLs by replacing them with a safe placeholder
    if 'Image Cover Link ' in df.columns:
        df['Image Cover Link '] = "https://via.placeholder.com/150"
    
    return df

# =============================================================================
# Execution Block
# =============================================================================
if __name__ == "__main__":
    print("Updating mockup data...")
    try:
        # Load the real dataset
        df = pd.read_excel(input_path)
        
        # Apply the anonymization transformation
        df_mocked = mock_data(df)
        
        # Save the result to the target destination
        df_mocked.to_excel(output_path, index=False)
        print("Done! Data updated with Pandora and Napster.")
    except Exception as e:
        print(f"Error during execution: {e}")

