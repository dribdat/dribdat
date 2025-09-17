from dribdat.aggregation import get_huggingface_project
from dribdat.apifetch import FetchHuggingFaceProject

def test_get_huggingface_project(testapp):
    """Test getting a Hugging Face project."""
    url = "https://huggingface.co/google-bert/bert-base-uncased"
    with testapp.app.app_context():
        data = get_huggingface_project(url)
    assert "name" in data
    assert data["name"] == "google-bert/bert-base-uncased"
    assert "description" in data
    assert "Bert" in data["description"]
    assert "commits" in data
    assert len(data["commits"]) > 0
