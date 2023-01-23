import json

class TsExceptionMixin(Exception):
    def __init__(self, message, error_message, error_code, **kwargs):
        self.message = message
        self.error_message = error_message
        self.error_code = error_code


class TSRespUnknownException(TsExceptionMixin):
    pass


class TSRespSuccessFalseException(TsExceptionMixin):
    pass


class TsRespInvalidOrExpiredSession(TsExceptionMixin):
    pass


def check_response(json_data):
    success = json_data.get('Success')

    if not success:
        error = json_data.get('Error')
        if error:
            msg = error.get('Message')
            err_msg = error.get('ErrorMessage')
            err_code = error.get('Code')
            param = {
                'message': msg,
                'error_message': err_msg,
                'error_code': err_code
            }
            if err_msg == 'Invalid or expired session':
                raise TsRespInvalidOrExpiredSession(**param)
            else:
                raise TSRespUnknownException(**param)
