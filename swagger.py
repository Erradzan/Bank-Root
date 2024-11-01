from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger_template = {
    "info": {
        "title": "Bank Root",
        "description": "API documentation for the Banking Application",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        },
    },
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
}

def init_swagger(app):
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    return swagger