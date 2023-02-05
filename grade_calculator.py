from enum import Enum
from itertools import chain, combinations
from typing import List, Tuple, Dict, Set, Iterable, TypeVar, Optional


# area tags
class Area(Enum):
    SUP = "SUP"  # support electives
    PRACTICAL = "PRACTICAL"
    THESIS = "THESIS"
    IDP = "IDP"
    GUIDED_RESEARCH = "GUIDED_RESEARCH"
    SEMINAR = "SEMINAR"

    ALG = "ALG"
    CGV = "CGV"
    DBI = "DBI"
    DBM = "DBM"
    SE = "SE"
    FMA = "FMA"
    MLA = "MLA"
    RRV = "RRV"
    ROB = "ROB"
    SP = "SP"
    HPC = "HPC"
    OTHER = "OTHER"


COURSE_AREAS = {Area.ALG, Area.CGV, Area.DBI, Area.DBM, Area.SE, Area.FMA, Area.MLA, Area.RRV, Area.ROB, Area.SP,
                Area.HPC, Area.OTHER}

# schema: (module name, area, ects, grade, THEO)
Grade = Tuple[str, Area, int, Optional[float], bool]
# enter your own grades in this list:
GRADES: List[Grade] = \
    [
        ("Thesis", Area.THESIS, 30, 1.0, False),

        ("IDP", Area.IDP, 16, 1.2, False),
        ("DiDaTra", Area.SUP, 4, None, False),
        ("C++", Area.PRACTICAL, 10, 1.0, False),
        ("ADLR", Area.MLA, 6, 1.7, False),

        ("CAML", Area.SEMINAR, 5, 1.0, False),
        ("BA", Area.MLA, 5, 1.8, False),
        ("Patterns", Area.SE, 5, 1.7, False),
        ("CA", Area.RRV, 6, 1.0, False),
        ("TWG", Area.SUP, 3, 1.3, False),

        ("ERDB", Area.DBI, 6, 1.0, False),
        ("MMDS", Area.MLA, 5, 1.5, False),
        ("ADL4CV", Area.CGV, 8, 1.3, False),
        ("Franz", Area.SUP, 3, 1.7, False),
        ("DDML", Area.PRACTICAL, 10, 1.0, False),

        ("NLP", Area.MLA, 6, 2.3, False),
        ("EAD", Area.ALG, 8, 1.3, True),
        ("I2DL", Area.MLA, 6, 2.0, False),
        ("ProgOpt", Area.FMA, 8, 2.3, True),
        ("itsec", Area.SP, 5, 2.7, False),
    ]

T = TypeVar("T")


def flatten(iterable: Iterable[Iterable[T]]) -> List[T]:
    return list(chain.from_iterable(iterable))


def power_set(grades: List[T]) -> List[List[T]]:
    res = flatten(combinations(grades, r) for r in range(len(grades) + 1))
    return list(map(lambda x: list(x), res))


def sum_of_credits(grades: List[Grade]) -> int:
    return sum(map(lambda x: x[2], grades))


def sum_of_theo_credits(grades: List[Grade]) -> int:
    return sum_of_credits(list(filter(lambda x: x[4], grades)))


def avg_grade(grades: List[Grade]) -> float:
    grades = list(filter(lambda x: x[3] is not None, grades))
    if len(grades) == 0:
        return 5.0
    return sum(map(lambda x: x[2] * x[3], grades)) / sum(map(lambda x: x[2], grades))


def map_to_areas(grades: List[Grade]) -> Dict[Area, List[Grade]]:
    res = {}
    for grade in grades:
        if grade[1] in res:
            res[grade[1]] += [grade]
        else:
            res[grade[1]] = [grade]
    return res


def get_best_fill(grades: List[Grade], ects: int) -> List[Grade]:
    return get_best_theo_fill(grades, ects, 0)


def is_minimal(grades: List[Grade], required_credits: int, required_theo_credits: int) -> bool:
    if sum_of_credits(grades) <= required_credits:
        return True
    else:
        residual_credits = sum_of_credits(grades) - required_credits
        residual_theo_credits = sum_of_theo_credits(grades) - required_theo_credits
        return not any(grade[2] <= residual_credits
                       and sum_of_theo_credits([grade]) <= residual_theo_credits
                       for grade in grades)


def get_best_theo_fill(grades: List[Grade], ects: int, required_theo_credits: int) -> List[Grade]:
    if sum_of_credits(grades) <= ects:
        return grades
    else:
        combs = power_set(grades)
        valid_combs = filter(lambda x: sum_of_credits(x) >= ects, combs)
        valid_combs = list(filter(lambda x: sum_of_theo_credits(x) >= required_theo_credits, valid_combs))
        valid_combs = list(filter(lambda x: is_minimal(x, ects, required_theo_credits), valid_combs))
        return sorted(valid_combs, key=lambda x: avg_grade(x))[0]


def get_all_elective_areas(grades: List[Grade]) -> Set[Area]:
    res = set(map(lambda x: x[1], grades)) - {Area.SUP, Area.IDP, Area.THESIS, Area.PRACTICAL,
                                              Area.GUIDED_RESEARCH}
    return res


def get_best_subfield(required_credits: int, by_areas: Dict[Area, List[Grade]], areas: Set[Area]) \
        -> Tuple[Area, List[Grade]]:
    possible_majors = [get_best_fill(by_areas[area], required_credits) for area in areas]
    if len(possible_majors) == 0:
        return Area.OTHER, []
    if max(map(lambda x: sum_of_credits(x), possible_majors)) < required_credits:
        best_major = sorted(possible_majors, key=lambda x: sum_of_credits(x))[-1]
    else:
        possible_majors = filter(lambda x: sum_of_credits(x) >= required_credits, possible_majors)
        best_major = sorted(possible_majors, key=lambda x: avg_grade(x))[0]
    return best_major[0][1], best_major


def get_improving_grades(current_grades: List[Grade], available_grades: List[Grade]) -> List[Grade]:
    available_grades.sort(key=lambda x: x[3])
    result = []
    while len(available_grades) > 0 and available_grades[0][3] < avg_grade(current_grades + result):
        result.append(available_grades.pop(0))
    return result


def get_free_choices(grades: List[Grade], credits_needed: int, theo_credits_needed: int,
                     other_grades: List[Grade]) -> List[Grade]:
    # choose a 2nd practical or a guided research if the grades are better
    res = []
    best_avg = get_best_fill(grades, credits_needed)
    best_pracs_grs = sorted(filter(lambda x: x[1] in (Area.PRACTICAL, Area.GUIDED_RESEARCH), grades),
                            key=lambda x: x[3])
    if len(best_pracs_grs) > 0 and best_pracs_grs[0][3] < avg_grade(best_avg):
        res += [best_pracs_grs[0]]
        credits_needed -= 10
        grades = list(set(grades) - set(best_pracs_grs))
    # choose courses to reach THEO credit limit
    res += get_best_theo_fill(grades, credits_needed, theo_credits_needed)
    # choose additional courses which might improve the grade
    grades = list(set(grades) - set(res))
    res += get_improving_grades(other_grades + res, grades)
    return res


def get_complete(grades: List[Grade], required_credits: int) -> bool:
    return sum_of_credits(grades) >= required_credits


def get_complete_str(grades: List[Grade], required_credits: int) -> str:
    if sum_of_credits(grades) >= required_credits:
        return "complete"
    else:
        return "incomplete"


def grade_to_str(grade: Grade) -> str:
    return f"{grade[0]}({grade[2]}): {grade[3]}, "


def print_grades(grades: List[Grade]):
    out = "".join(map(grade_to_str, grades))
    print("[" + out[:-2] + "]")


def compute_grade(grades: List[Grade]):
    by_areas = map_to_areas(grades)

    # thesis
    thesis_grades = get_best_fill(by_areas.get(Area.THESIS, []), 30)
    print("Thesis", f"{avg_grade(thesis_grades):.3f}", get_complete_str(thesis_grades, 30))
    print_grades(thesis_grades)
    thesis_complete = get_complete(thesis_grades, 30)

    # idp
    idp_grade = get_best_fill(by_areas.get(Area.IDP, []), 16)
    print("IDP", f"{avg_grade(idp_grade):.3f}", get_complete_str(idp_grade, 16))
    idp_complete = get_complete(idp_grade, 16)

    # support electives
    sup_grades = get_best_fill(by_areas.get(Area.SUP, []), 6)
    print("support electives:", f"{avg_grade(sup_grades):.3f}", get_complete_str(sup_grades, 6))
    print_grades(sup_grades)
    sup_complete = get_complete(sup_grades, 6)

    # practical
    prac_1_grades = get_best_fill(by_areas.get(Area.PRACTICAL, []), 10)
    print("practical:", f"{avg_grade(prac_1_grades):.3f}", get_complete_str(prac_1_grades, 10))
    print_grades(prac_1_grades)
    prac_complete = get_complete(prac_1_grades, 10)

    # seminar
    seminar_grades = get_best_fill(by_areas.get(Area.SEMINAR, []), 5)
    print("Seminar: ", f"{avg_grade(seminar_grades):.3f}", get_complete_str(seminar_grades, 5))
    print_grades(seminar_grades)
    seminar_complete = get_complete(seminar_grades, 5)

    areas = get_all_elective_areas(grades)

    # major
    major_credits = 18
    major_name, major_grades = get_best_subfield(major_credits, by_areas, areas)
    areas -= {major_name}
    print("major:", major_name, f"{avg_grade(major_grades):.3f}", get_complete_str(major_grades, 18))
    print_grades(major_grades)
    major_complete = get_complete(major_grades, major_credits)
    major_credit_excess = max(0, sum_of_credits(major_grades) - major_credits)

    minor_credits = 8
    # 1st minor
    minor_1_name, minor_1_grades = get_best_subfield(minor_credits, by_areas, areas)
    areas -= {minor_1_name}
    print("1st minor:", minor_1_name, f"{avg_grade(minor_1_grades):.3f}", get_complete_str(minor_1_grades, 8))
    print_grades(minor_1_grades)
    minor_1_complete = get_complete(minor_1_grades, 8)
    minor_1_credit_excess = max(0, sum_of_credits(minor_1_grades) - minor_credits)

    # 2nd minor
    minor_2_name, minor_2_grades = get_best_subfield(minor_credits, by_areas, areas)
    areas -= {minor_2_name}
    print("2nd minor:", minor_2_name, f"{avg_grade(minor_2_grades):.3f}", get_complete_str(minor_2_grades, 8))
    print_grades(minor_2_grades)
    minor_2_complete = get_complete(minor_2_grades, 8)
    minor_2_credit_excess = max(0, sum_of_credits(minor_2_grades) - minor_credits)

    all_grades = [thesis_grades,
                  idp_grade,
                  sup_grades,
                  prac_1_grades,
                  seminar_grades,
                  major_grades,
                  minor_1_grades,
                  minor_2_grades]

    # free choices
    available_grades = set(flatten([by_areas.get(area, []) for area in COURSE_AREAS]))
    available_grades |= set(by_areas.get(Area.PRACTICAL, []))
    available_grades |= set(by_areas.get(Area.GUIDED_RESEARCH, []))
    available_grades = list(available_grades
                            - set(sup_grades)
                            - set(major_grades)
                            - set(minor_1_grades)
                            - set(minor_2_grades)
                            - set(prac_1_grades))
    credits_needed = 19 - sum((major_credit_excess, minor_1_credit_excess, minor_2_credit_excess))
    theo_credits_needed = 10 - sum_of_theo_credits(major_grades + minor_1_grades + minor_2_grades)
    free_choice_grades = get_free_choices(available_grades, credits_needed, theo_credits_needed, flatten(all_grades))
    print("free choices:", f"{avg_grade(free_choice_grades):.3f}", get_complete_str(free_choice_grades, credits_needed))
    print_grades(free_choice_grades)
    free_choices_complete = get_complete(free_choice_grades, credits_needed)

    all_completions = [thesis_complete,
                       idp_complete,
                       sup_complete,
                       prac_complete,
                       seminar_complete,
                       major_complete,
                       minor_1_complete,
                       minor_2_complete,
                       free_choices_complete]

    all_grades.append(free_choice_grades)

    final_grade = avg_grade(flatten(all_grades))

    all_grades_flattened = flatten(all_grades)
    print("\nMasters Programm complete:", all(all_completions))
    print(f"theo credits reached: {sum_of_theo_credits(all_grades_flattened) > 10}: "
          f"{sum_of_theo_credits(all_grades_flattened)}/10")

    print(f"final grade: {final_grade:.3f}")

    non_contributing_courses = list(set(grades) - set(all_grades_flattened))
    print("\nnon contributing courses:")
    print_grades(non_contributing_courses)


if __name__ == '__main__':
    print(f"Credit sum of all contributing modules: {sum_of_credits(GRADES)}")
    compute_grade(GRADES)
