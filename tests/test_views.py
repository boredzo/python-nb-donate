import pytest
import git
import json
from donate.models import (
    Account,
    Currency,
    Project,
)
from donate.routes import get_donation_params


def validate_main_page_data(data):
    assert "donation-form" in data
    assert 'charge[amount]' in data
    assert 'cc-number' in data
    assert 'data-stripe' in data
    assert 'cc-exp' in data
    assert 'cvc' in data
    assert 'charge[recurring]' in data
    assert 'donor[email]' in data
    assert 'donation-form-name' in data
    assert 'donation-form-anonymous' in data
    assert 'donor[anonymous]' in data
    assert 'donor[name]' in data
    assert 'bitcoin' in data


def test_view_main(testapp):
    app = testapp
    result = app.get('/')
    assert result.status_code == 200
    data = result.data.decode('utf-8')
    validate_main_page_data(data)

    result = app.get('/index')
    assert result.status_code == 200
    data = result.data.decode('utf-8')
    validate_main_page_data(data)


def test_view_thanks(testapp):
    app = testapp

    result = app.get('/thanks')

    data = result.data.decode('utf-8')
    assert result.status_code == 200
    assert "humbled" in data
    assert "thankful" in data


def test_view_new_project_get(testapp):
    app = testapp

    result = app.get('/new/project')
    assert result.status_code == 200
    data = result.data.decode('utf-8')
    assert '<form action="/new/project" method="POST">' in data
    assert "Project Name" in data
    assert '<input class="project-name"' in data
    assert "Goal" in data
    assert '<input class="project-goal"' in data
    assert "Currency" in data
    assert '<input class="project-currency"' in data
    assert "Description" in data
    assert '<input class="project-description' in data
    assert '<input type="submit"' in data


def test_view_new_project_post(testapp, db):
    app = testapp

    project_name = "Test Project"
    ccy_code = "USD"
    ccy_name = "US Dollar"
    amt = 4000
    proj_desc = "A test project"

    ccy = Currency(code=ccy_code, name=ccy_name)
    db.session.add(ccy)

    db.session.commit()

    data = {
        'goal': amt,
        'ccy': ccy_code,
        'desc': proj_desc,
        'project_name': project_name,
    }
    url = "/new/project"
    response = app.post(url, data=data)

    project = db.session.query(Project).filter_by(name=project_name).one()
    assert project is not None
    assert project.name == project_name
    assert project.desc == proj_desc
    assert project.goal == amt

    accounts = project.accounts
    assert accounts is not None
    assert len(accounts) == 1

    acct = accounts[0]
    assert acct.name == "{}_{}_acct".format(project_name, ccy_code)

    ccy = acct.ccy
    assert ccy.code == ccy_code
    assert ccy.name == ccy_name

    assert response.status_code == 200


@pytest.mark.usefixtures('test_db_project')
def test_projects_page(testapp, db):
    app = testapp

    response = app.get('/projects')
    assert response.status_code == 200

    proj = db.session.query(Project).one()

    data = response.data.decode('utf-8')
    assert proj.name in data


@pytest.mark.usefixtures('test_db_project')
def test_one_project_page(testapp, db):
    app = testapp

    proj = db.session.query(Project).one()

    response = app.get('/projects/{}'.format(proj.name))

    assert response.status_code == 200

    data = response.data.decode('utf-8')

    assert proj.name in data
    assert str(proj.goal) in data


def test_get_donation_params(testapp, test_form):
    app = testapp

    result = get_donation_params(test_form)
