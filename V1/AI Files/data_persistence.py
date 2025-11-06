import pickle
import gzip
import os
from datetime import datetime

# --- Project Root Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def save_classification_data(page_classifications, raw_responses, filename="classifications.pkl.gz"):
    """
    Save classification data as compressed pickle file in the project directory.
    
    Args:
        page_classifications (dict): Structured classification results
        raw_responses (dict): Raw AI response data
        filename (str): Name for the pickle file
    
    Returns:
        str: Path to saved pickle file
    """
    # Save in the project root directory (e.g., 'Version One')
    pickle_path = os.path.join(PROJECT_ROOT, filename)
    
    # Prepare data for saving
    save_data = {
        'page_classifications': page_classifications,
        'raw_responses': raw_responses,
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_pages': len(page_classifications),
            'categories': {}
        }
    }
    
    # Calculate category statistics
    for page_data in page_classifications.values():
        category = page_data['category']
        save_data['metadata']['categories'][category] = save_data['metadata']['categories'].get(category, 0) + 1
    
    # Save as compressed pickle (fastest loading)
    with gzip.open(pickle_path, 'wb') as f:
        pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"Classification data saved to: {pickle_path}")
    return pickle_path

def load_classification_data(filename="classifications.pkl.gz"):
    """
    Load classification data from compressed pickle file in project directory.
    
    Args:
        filename (str): Name of the pickle file to load
    
    Returns:
        tuple: (page_classifications, raw_responses, metadata)
    """
    # Load from the project root directory (e.g., 'Version One')
    pickle_path = os.path.join(PROJECT_ROOT, filename)
    
    try:
        with gzip.open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        print(f"Loaded data from pickle file: {pickle_path}")
        return data['page_classifications'], data['raw_responses'], data['metadata']
    except FileNotFoundError:
        raise FileNotFoundError(f"Classification data file not found: {pickle_path}")
    except (pickle.PickleError, gzip.BadGzipFile) as e:
        raise Exception(f"Error loading pickle file: {e}")
