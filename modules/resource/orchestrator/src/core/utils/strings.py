class StringUtils:
    """
    Contains common operations related to string processing.
    """

    @staticmethod
    def find_all(string, substring):
        start = 0
        while True:
            start = string.find(substring, start)
            if start == -1: return
            yield start
            start += len(substring) # use start += 1 to find overlapping matches
