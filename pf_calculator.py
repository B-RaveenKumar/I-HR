"""PF calculation helpers aligned with EPFO rules."""

from typing import Dict

PF_EMPLOYEE_RATE = 0.12
PF_EMPLOYER_TOTAL_RATE = 0.12
EPS_RATE = 0.0833
EDLI_RATE = 0.005
ADMIN_RATE = 0.005
PF_WAGE_LIMIT = 15000.0
EPS_MAX = 1250
EDLI_MAX = 75
PF_COMPANY_THRESHOLD = 20


def _round_to_int(value: float) -> int:
    """Round positive monetary values to nearest integer using half-up."""
    if value <= 0:
        return 0
    return int(value + 0.5)


def calculate_pf_components(
    basic_salary: float,
    dearness_allowance: float = 0.0,
    pf_opt_in: bool = False,
    company_employee_count: int = 0,
) -> Dict[str, int]:
    """Calculate PF breakdown using EPFO-style rules.

    Rules:
    - PF applicable only when employee count >= 20.
    - PF wage = basic + DA.
    - Mandatory when PF wage <= 15000.
    - If PF wage > 15000, apply only when pf_opt_in is True.
    - Employee PF = 12% of PF wage.
    - Employer total = 12% of PF wage.
    - EPS = 8.33% of min(PF wage, 15000), capped at 1250.
    - Employer EPF = employer total - EPS.
    - EDLI = 0.5% of PF wage, capped at 75.
    - Admin = 0.5% of PF wage.
    """

    basic = max(0.0, float(basic_salary or 0.0))
    da = max(0.0, float(dearness_allowance or 0.0))
    pf_wage = basic + da

    company_pf_applicable = int(company_employee_count or 0) >= PF_COMPANY_THRESHOLD
    mandatory_pf = pf_wage <= PF_WAGE_LIMIT
    pf_applicable = company_pf_applicable and (mandatory_pf or bool(pf_opt_in))

    if not pf_applicable:
        return {
            'pf_wage': _round_to_int(pf_wage),
            'employee_pf': 0,
            'employer_epf': 0,
            'eps': 0,
            'edli': 0,
            'admin_charges': 0,
            'company_pf_applicable': 1 if company_pf_applicable else 0,
            'mandatory_pf': 1 if mandatory_pf else 0,
            'pf_opt_in': 1 if pf_opt_in else 0,
            'pf_applicable': 0,
        }

    employee_pf_raw = pf_wage * PF_EMPLOYEE_RATE
    employer_total_raw = pf_wage * PF_EMPLOYER_TOTAL_RATE

    eps_base = min(pf_wage, PF_WAGE_LIMIT)
    eps_raw = min(eps_base * EPS_RATE, EPS_MAX)

    edli_raw = min(pf_wage * EDLI_RATE, EDLI_MAX)
    admin_raw = pf_wage * ADMIN_RATE

    employee_pf = _round_to_int(employee_pf_raw)
    employer_total = _round_to_int(employer_total_raw)
    eps = _round_to_int(eps_raw)
    employer_epf = max(0, employer_total - eps)

    return {
        'pf_wage': _round_to_int(pf_wage),
        'employee_pf': employee_pf,
        'employer_epf': employer_epf,
        'eps': eps,
        'edli': _round_to_int(edli_raw),
        'admin_charges': _round_to_int(admin_raw),
        'company_pf_applicable': 1 if company_pf_applicable else 0,
        'mandatory_pf': 1 if mandatory_pf else 0,
        'pf_opt_in': 1 if pf_opt_in else 0,
        'pf_applicable': 1,
    }
