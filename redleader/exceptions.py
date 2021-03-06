# MIT License

# Copyright (c) 2016 Morgan McDermott & John Carlyle

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class RedLeaderError(Exception):
    """
    Base exception for all redleader exceptions
    """

    message = 'An unknown error has occured'

    def __init__(self, **kwargs):
        msg = self.message.format(**kwargs)
        Exception.__init__(self, msg)
        self.kwargs = kwargs


class MissingDependencyError(RedLeaderError):
    message = 'Resource {source_resource} missing dependency {missing_resource}. Ensure {missing_resource} has been added to the cluster.'

class OfflineContextError(RedLeaderError):
    message = 'Attempting to use offline context like an online context.'

class OfflineContextError(RedLeaderError):
    message = 'OfflineContext cannot perform action {action}'
