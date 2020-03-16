class Proxy:
    def __init__(self, host, port):
        self.host=host
        self.port=port
        self.succeed=0
        self.fail=0

    def markSucceed(self):
        self.succeed +=1

    def markFail(self):
        self.fail +=1

    def __str__(self):
        return f'http://{self.host}:{self.port}'
