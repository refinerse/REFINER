import re


def test_ser_deser_uses_jsonserializer_on_component_not_model_dump_dict():
    """
    Regression test for review comment:
    ensure serialization happens on the Mem0Memory component itself
    (so JsonSerializer can detect components/pydantic objects),
    rather than serializing the dict returned by model_dump().
    """
    path = "/workspace/llama-index-integrations/memory/llama-index-memory-mem0/tests/test_mem0.py"
    source = open(path, "r", encoding="utf-8").read()

    # The behavioral change is that the test now calls:
    #   JsonSerializer().serialize(mem0_memory)
    # instead of:
    #   JsonSerializer().serialize(element)
    assert (
        "JsonSerializer().serialize(mem0_memory)" in source
    ), "Expected test to serialize the Mem0Memory object directly: JsonSerializer().serialize(mem0_memory)"

    assert (
        "JsonSerializer().serialize(element)" not in source
    ), "Serializer should not be invoked on the model_dump() dict ('element'); it must receive the component"

    # Additional guard: ensure the component wrapper payload is asserted (component-aware serialization)
    assert '"__is_component": True' in source, (
        "Expected assertion that serialized output is a component-aware JSON payload "
        '(contains "__is_component": True), indicating JsonSerializer handled the object properly.'
    )

    # Ensure the qualified name is asserted for the component serialization
    assert re.search(r'qualified_name"\s*:\s*"llama_index\.memory\.mem0\.base\.Mem0Memory"', source), (
        "Expected serialized payload to assert the fully qualified name for Mem0Memory "
        '("llama_index.memory.mem0.base.Mem0Memory").'
    )