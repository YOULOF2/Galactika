EMAIL_ERROR = "That email does not exist, please try again."
PASSWORD_ERROR = "Password incorrect, please try again."
ALREADY_LOGGED_IN_ERROR = "You've already signed up with that email, log in instead"
COMMENT_LOGIN_ERROR = "You need to register or login to comment."
ERROR_CODES = {
    "404": {
        "code": 404,
        "expression": "Oops!",
        "title": "Page not found",
        "description": "The page you are looking for might have been removed had its name changed or is temporarily "
                       "unavailable. "
    },
    "403": {
        "code": 403,
        "expression": "Naughty!",
        "title": "Forbidden",
        "description": "You don't have the permission to access the requested resource. It is either read-protected "
                       "or not readable by the server. "
    },
    "500": {
        "code": 500,
        "expression": "Sorry!",
        "title": "Technical Difficulties",
        "description": "Where facing some technical difficulties. Please try again later."
    }
}
