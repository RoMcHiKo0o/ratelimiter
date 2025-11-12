START CMD /k uvicorn main:app --reload

START CMD /k uvicorn "tests.limited_api":app --port 8889 --reload
