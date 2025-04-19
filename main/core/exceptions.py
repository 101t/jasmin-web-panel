from rest_framework.exceptions import APIException


class TelnetUnexpectedResponse(APIException):
    status_code = 500
    default_detail = 'Unexpected response from Jasmin'


class TelnetConnectionTimeout(APIException):
    status_code = 500
    default_detail = 'Connection to jcli timed out'


class TelnetLoginFailed(APIException):
    status_code = 403
    default_detail = 'Jasmin login failed'


class CanNotModifyError(APIException):
    status_code = 400
    default_detail = 'Can not modify a key'


class JasminSyntaxError(APIException):
    status_code = 400
    default_detail = 'Can not modify a key'


class JasminError(APIException):
    status_code = 400
    default_detail = 'Jasmin error'


class UnknownError(APIException):
    status_code = 404
    default_detail = 'object not known'


class MissingKeyError(APIException):
    status_code = 400
    default_detail = 'A mandatory key is missing'


class MultipleValuesRequiredKeyError(APIException):
    status_code = 400
    default_detail = 'Multiple values are required fro this key'


class ActionFailed(APIException):
    status_code = 400
    default_detail = 'Action failed'


class ObjectNotFoundError(APIException):
    status_code = 404
    default_detail = 'Object not found'


class DuplicateEntryError(APIException):
    status_code = 400
    default_detail = 'Duplicate entry'


class ValidationError(APIException):
    status_code = 400
    default_detail = 'Validation error'