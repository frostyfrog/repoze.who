import unittest

class _Base(unittest.TestCase):

    def failUnless(self, predicate, message=''):
        self.assertTrue(predicate, message) # Nannies go home!

    def failIf(self, predicate, message=''):
        self.assertFalse(predicate, message) # Nannies go home!

class AuthenticatedPredicateTests(_Base):

    def _getFUT(self):
        from repoze.who.restrict import authenticated_predicate
        return authenticated_predicate()

    def test___call___no_identity_returns_False(self):
        predicate = self._getFUT()
        environ = {}
        self.failIf(predicate(environ))

    def test___call___w_REMOTE_AUTH_returns_True(self):
        predicate = self._getFUT()
        environ = {'REMOTE_USER': 'fred'}
        self.failUnless(predicate(environ))

    def test___call___w_repoze_who_identity_returns_True(self):
        predicate = self._getFUT()
        environ = {'repoze.who.identity': {'login': 'fred'}}
        self.failUnless(predicate(environ))

class MakeAuthenticatedRestrictionTests(_Base):

    def _getFUT(self):
        from repoze.who.restrict import make_authenticated_restriction
        return make_authenticated_restriction

    def test_enabled(self):
        fut = self._getFUT()
        app = DummyApp()

        filter = fut(app, {}, enabled=True)

        self.failUnless(filter.app is app)
        self.failUnless(filter.enabled)
        predicate = filter.predicate
        self.failUnless(predicate({'REMOTE_USER': 'fred'}))
        self.failUnless(predicate({'repoze.who.identity': {'login': 'fred'}}))

class PredicateRestrictionTests(_Base):

    def _getTargetClass(self):
        from repoze.who.restrict import PredicateRestriction
        return PredicateRestriction

    def _makeOne(self, app=None, **kw):
        if app is None:
            app = DummyApp()
        return self._getTargetClass()(app, **kw)

    def test___call___disabled_predicate_false_calls_app_not_predicate(self):
        _tested = []
        def _factory():
            def _predicate(env):  # pragma: no cover
                assert False
            return _predicate

        def _start_response(status, headers):
            assert False  # pragma: no cover
        environ = {'testing': True}

        restrict = self._makeOne(predicate=_factory, enabled=False)
        restrict(environ, _start_response)

        self.assertEqual(len(_tested), 0)
        self.assertEqual(restrict.app.environ, environ)

    def test___call___enabled_predicate_false_returns_401(self):
        _tested = []
        def _factory():
            def _predicate(env):
                _tested.append(env)
                return False
            return _predicate

        _started = []
        def _start_response(status, headers):
            _started.append((status, headers))
        environ = {'testing': True}

        restrict = self._makeOne(predicate=_factory)
        restrict(environ, _start_response)

        self.assertEqual(len(_tested), 1)
        self.assertEqual(len(_started), 1, _started)
        self.assertEqual(_started[0][0], '401 Unauthorized')
        self.assertEqual(restrict.app.environ, None)

    def test___call___enabled_predicate_true_calls_app(self):
        _tested = []
        def _factory():
            def _predicate(env):
                _tested.append(env)
                return True
            return _predicate

        def _start_response(status, headers):
            assert False  # pragma: no cover
        environ = {'testing': True, 'REMOTE_USER': 'fred'}

        restrict = self._makeOne(predicate=_factory)
        restrict(environ, _start_response)

        self.assertEqual(len(_tested), 1)
        self.assertEqual(restrict.app.environ, environ)

class MakePredicateRestrictionTests(_Base):

    def _getFUT(self):
        from repoze.who.restrict import make_predicate_restriction
        return make_predicate_restriction

    def test_non_string_predicate_no_args(self):
        fut = self._getFUT()
        app = DummyApp()
        def _predicate(env):
            return True  # pragma: no cover
        def _factory():
            return _predicate

        filter = fut(app, {}, predicate=_factory)

        self.failUnless(filter.app is app)
        self.failUnless(filter.predicate is _predicate)
        self.failUnless(filter.enabled)

    def test_disabled_non_string_predicate_w_args(self):
        fut = self._getFUT()
        app = DummyApp()

        filter = fut(app, {}, predicate=DummyPredicate, enabled=False,
                     foo='Foo')

        self.failUnless(filter.app is app)
        self.failUnless(isinstance(filter.predicate, DummyPredicate))
        self.assertEqual(filter.predicate.foo, 'Foo')
        self.failIf(filter.enabled)

    def test_enabled_string_predicate_w_args(self):
        fut = self._getFUT()
        app = DummyApp()

        filter = fut(app, {},
                     predicate='repoze.who.tests.test_restrict:DummyPredicate',
                     enabled=True, foo='Foo')

        self.failUnless(filter.app is app)
        self.failUnless(isinstance(filter.predicate, DummyPredicate))
        self.assertEqual(filter.predicate.foo, 'Foo')
        self.failUnless(filter.enabled)


class DummyApp(object):
    environ = None
    def __call__(self, environ, start_response):
        self.environ = environ
        return []

class DummyPredicate(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
