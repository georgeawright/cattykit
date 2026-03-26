from copycat.codelets.scout import Scout


class RuleScout(Scout):
    """Fills in the rule template "Replace ___ by ___ " by choosing descriptions of
    the changed object in the initial string and its replacement in the modified string.
    If the rule can be made, it proposes it and posts a rule strength tester
    with urgency a function of the conceptual depth of the descriptions."""

    pass
