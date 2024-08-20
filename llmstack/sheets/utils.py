from pyparsing import (
    Group,
    ParseException,
    QuotedString,
    Suppress,
    Word,
    alphanums,
    alphas,
    delimitedList,
    nums,
)

# Define grammar
identifier = Word(alphas, alphanums + "_")  # Function name or other identifiers
number = Word(nums)  # Numbers (integers)
cell_identifier = Word(nums) + Suppress("-") + Word(nums)  # Cell identifier like '1-1'

# Handle string parameters, including quoted strings
string_param = QuotedString('"') | QuotedString("'")  # Strings enclosed in quotes
parameter = cell_identifier | number | string_param | identifier

lparen = Suppress("(")
rparen = Suppress(")")
comma = Suppress(",")
equal = Suppress("=")

function_name = identifier
parameters = Group(delimitedList(parameter))

function_call = equal + function_name + lparen + parameters + rparen


def parse_formula(value):
    try:
        parsed = function_call.parseString(value)
        function_name = parsed[0]
        parameters = parsed[1].asList()
        return function_name, parameters
    except ParseException:
        return None, None
