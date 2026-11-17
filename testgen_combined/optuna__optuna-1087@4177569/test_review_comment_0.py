import optuna.integration.chainermn as chainermn


class _DummyMPIComm:
    def bcast(self, value):
        # Rank 0 path: bcast just returns whatever was passed.
        return value

    def barrier(self):
        return None


class _DummyComm:
    rank = 0
    mpi_comm = _DummyMPIComm()


class _DummyDelegateTrial:
    def suggest_float(self, name, low, high, *, log=False):
        # If ChainerMNTrial does not forward `log`, this will stay False.
        return 123.0 if log else 456.0


def test_chainermntrial_suggest_float_forwards_log_kwarg():
    trial = chainermn.ChainerMNTrial(_DummyDelegateTrial(), _DummyComm())

    got = trial.suggest_float("x", 1.0, 10.0, log=True)

    assert (
        got == 123.0
    ), "ChainerMNTrial.suggest_float should forward the `log` keyword argument to the delegate trial."