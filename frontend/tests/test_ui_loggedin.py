import os
import json


def test_recommendations_page_logged_in(page):
    # Prepare paths
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    file_path = 'file://' + os.path.join(repo_root, 'frontend', 'pages', 'recommendations.html')

    # Preconfigure localStorage on page init so origin restrictions avoid errors
    page.add_init_script("""
        window.localStorage.setItem('token','testtoken');
        window.localStorage.setItem('userType','patient');
    """
    )

    # Intercept health-info and recommendations endpoints and return mocked JSON
    health_info = {
        'health_conditions': {'diabetes': '130', 'cholesterol': '210'},
        'allergies': [],
        'food_preference': 'vegetarian'
    }

    rec_resp = {
        'food': {
            'morning': [{'name': 'Oatmeal', 'reason': 'High fiber helps glucose control'}],
            'afternoon': [],
            'evening': []
        },
        'drinks': [{'name': 'Warm Lemon Water', 'reason': 'Hydration and metabolism boost'}],
        'snacks': [{'name': 'Carrot Sticks', 'reason': 'Low calorie and filling'}],
        'foods_to_avoid': [{'name': 'Fried rice', 'reason': 'High fat'}],
        'healthy_tips': {'hydration': 'Drink 8 glasses of water'}
    }

    # Route network calls to stubbed JSON responses
    page.route("**/api/patient/health-information", lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps(health_info)))
    page.route("**/api/recommendations/get", lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps(rec_resp)))
    # stub alternatives endpoint with dataset items
    # only one alternative should be returned
    alt_resp = {'category': 'food', 'alternatives': [
        {'name': 'Steamed Vegetables', 'reason': 'Healthy and low calorie'}
    ], 'count': 1}
    page.route("**/api/recommendations/alternatives", lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps(alt_resp)))

    # also define a simplified payload (strings only) for an additional check
    # simplified payload mimicking server-side '/get' output; includes
    # lunch/dinner keys to test aliasing and an empty drinks list so we can
    # verify the front-end handles the no-drinks case gracefully.
    simple_resp = {
        'Food': {
            'morning': [{'name': 'Scrambled eggs', 'reason': 'Protein'}],
            'lunch': [{'name': 'Salad', 'reason': 'Light and fresh'}],
            'dinner': []
        },
        'Drinks': [],
        'Snacks': [],
        'foods_to_avoid': [],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {}
    }
    # we'll call this via a second navigation step below

    # Load the page (now with localStorage and mocked network)
    page.goto(file_path)

    # Wait for the food recommendation to appear
    page.wait_for_selector('#foodContent .recommendation-item', timeout=5000)

    # assert the normal (object) recommendation text exists
    const_name = page.locator('#foodContent .recommendation-item-name').first.text_content()
    assert 'Oatmeal' in const_name

    # Assert healthy tips are shown (before we change the payload)
    tip = page.locator('#tipsContent .tip-item').first.text_content()
    assert 'Drink 8 glasses' in tip

    # foods-to-avoid block should be rendered as well (before payload change)
    page.wait_for_selector('#avoidContent .recommendation-item', timeout=5000)
    avoid_name = page.locator('#avoidContent .recommendation-item-name').first.text_content()
    assert 'Fried rice' in avoid_name

    # now simulate simplified response by intercepting and invoking loadRecommendations again
    page.route("**/api/recommendations/get", lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps(simple_resp)))
    # call the existing JS function to refresh recommendations
    page.evaluate("loadRecommendations();")
    page.wait_for_selector('#foodContent .recommendation-item', timeout=5000)
    # ensure the new payload actually arrived in the page
    last = page.evaluate("() => window._lastRecommendation");
    assert last == simple_resp
    # now check that the rendering logic handled object items with reasons
    assert 'Scrambled eggs' in page.locator('#foodContent .recommendation-item-name').first.text_content()
    assert 'Protein' in page.locator('#foodContent .recommendation-item-reason').first.text_content()
    # lunch alias should also have been rendered
    assert 'Salad' in page.locator('#foodContent').text_content()

    # drinks list was empty in the payload; UI should show the placeholder text
    drinks_text = page.locator('#drinksContent').text_content()
    assert 'No recommendations available' in drinks_text

    # the default healthy tips block should appear
    tips_text = page.locator('#tipsContent').text_content()
    assert 'Hydration' in tips_text and 'Physical Activity' in tips_text

    # inline alternatives should appear automatically beneath food recommendations
    page.wait_for_selector('#foodContent .alternative-item', timeout=5000)
    inline_name = page.locator('#foodContent .alternative-item .recommendation-item-name').first.text_content()
    assert inline_name == 'Steamed Vegetables'
    # Now test alternatives dataset path; it may already be visible or require
    # a click depending on whether auto-show behavior ran.
    if not page.is_visible('#foodAlternatives .alternative-item'):
        page.click("button[onclick*=\"toggleAlternatives('food')\"]")
    # wait for alternatives to load (either way)
    page.wait_for_selector('#foodAlternatives .alternative-item', timeout=5000)
    alt_name = page.locator('#foodAlternatives .item-name').first.text_content()
    # should be one of our seeded items
    assert alt_name == 'Steamed Vegetables'
