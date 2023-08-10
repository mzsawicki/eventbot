from eventbot.domain import ports, vo


def create_code_for_event(event_name: str, sequence_generator: ports.EventSequenceGenerator) -> vo.EventCode:
    alpha_part = event_name.lower()[:3]
    numeral_part = next(sequence_generator())
    code = vo.EventCode(f'{alpha_part}-{numeral_part}')
    return code
