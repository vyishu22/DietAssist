import os


def test_recommendations_page_title(page):
    # pre-populate localStorage to bypass auth redirect
    page.add_init_script("""
        window.localStorage.setItem('token', 'fake-token');
        window.localStorage.setItem('userType', 'patient');
    """
    )
    # Load the local recommendations HTML file using a file:// URL
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    file_path = 'file://' + os.path.join(repo_root, 'frontend', 'pages', 'recommendations.html')
    page.goto(file_path)
    assert 'Your Recommendations - DietAssist' in page.title()
