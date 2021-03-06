from enum import Enum
from itertools import chain, combinations
from typing import List, Tuple, Dict, Set, Iterable, TypeVar


# area tags
class Area(Enum):
    SUP = "SUP"  # support electives
    PRACTICAL = "PRACTICAL"
    THESIS = "THESIS"
    IDP = "IDP"
    IDP_LECTURE = "IDP_LECTURE"
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
Grade = Tuple[str, Area, int, float, bool]
# enter your own grades in this list:
grades: List[Grade] = \
    [("ERDB", Area.DBI, 6, 1.0, False),
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


def flatten(l: Iterable[Iterable[T]]) -> List[T]:
    return list(chain.from_iterable(l))


def power_set(grades: List[T]) -> List[List[T]]:
    res = flatten(combinations(grades, r) for r in range(len(grades) + 1))
    return list(map(lambda x: list(x), res))


def sum_of_credits(grades: List[Grade]) -> int:
    return sum(map(lambda x: x[2], grades))


def sum_of_theo_credits(grades: List[Grade]) -> int:
    return sum_of_credits(list(filter(lambda x: x[4], grades)))


def avg_grade(grades: List[Grade]) -> float:
    if len(grades) == 0: return 5.0
    return sum(map(lambda x: x[2] * x[3], grades)) / sum(map(lambda x: x[2], grades))


def map_to_areas(grades: List[Grade]) -> Dict[Area, List[Grade]]:
    res = {}
    for grade in grades:
        if grade[1] in res:
            res[grade[1]] += [grade]
        else:
            res[grade[1]] = [grade]
    return res


def get_best_fill(grades: List[Grade], credits: int) -> List[Grade]:
    return get_best_theo_fill(grades, credits, 0)


def is_minimal(grades: List[Grade], required_credits: int) -> bool:
    if sum_of_credits(grades) <= required_credits:
        return True
    else:
        return min([grade[2] for grade in grades]) > sum_of_credits(grades) - required_credits


def get_best_theo_fill(grades: List[Grade], credits: int, required_theo_credits: int) -> List[Grade]:
    if sum_of_credits(grades) <= credits:
        return grades
    else:
        combs = power_set(grades)
        valid_combs = filter(lambda x: sum_of_credits(x) >= credits, combs)
        valid_combs = list(filter(lambda x: sum_of_theo_credits(x) >= required_theo_credits, valid_combs))
        valid_combs = list(filter(lambda x: is_minimal(x, credits), valid_combs))
        return sorted(valid_combs, key=lambda x: avg_grade(x))[0]


def get_all_elective_areas(grades: List[Grade]) -> Set[Area]:
    res = set(map(lambda x: x[1], grades)) - {Area.SUP, Area.IDP, Area.IDP_LECTURE, Area.THESIS, Area.PRACTICAL,
                                              Area.GUIDED_RESEARCH}
    return res


def get_best_major(by_areas: Dict[Area, List[Grade]], areas: Set[Area]) -> Tuple[Area, List[Grade]]:
    major_credits = 18
    possible_majors = [get_best_fill(by_areas[area], major_credits) for area in areas]
    if len(possible_majors) == 0:
        return Area.OTHER, []
    if max(map(lambda x: sum_of_credits(x), possible_majors)) < major_credits:
        best_major = sorted(possible_majors, key=lambda x: sum_of_credits(x))[-1]
    else:
        possible_majors = filter(lambda x: sum_of_credits(x) >= major_credits, possible_majors)
        best_major = sorted(possible_majors, key=lambda x: avg_grade(x))[0]
    return best_major[0][1], best_major


def get_best_minor(by_areas: Dict[Area, List[Grade]], areas: Set[Area]) -> Tuple[Area, List[Grade]]:
    minor_credits = 8
    possible_minors = [get_best_fill(by_areas[area], minor_credits) for area in areas]
    if len(possible_minors) == 0:
        return Area.OTHER, []
    if max(map(lambda x: sum_of_credits(x), possible_minors)) < minor_credits:
        best_minor = sorted(possible_minors, key=lambda x: sum_of_credits(x))[-1]
    else:
        possible_minors = filter(lambda x: sum_of_credits(x) >= minor_credits, possible_minors)
        best_minor = sorted(possible_minors, key=lambda x: avg_grade(x))[0]
    return best_minor[0][1], best_minor


def get_free_choices(grades: List[Grade], credits_needed: int, theo_credits_needed: int) -> List[Grade]:
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
    return res


def get_reweight_grade(grades: List[List[Grade]], expected_credits: List[int]) -> float:
    assert len(grades) == len(expected_credits)
    if sum(expected_credits) == 0:
        return 5.0
    grades = list(map(lambda x: avg_grade(x), grades))
    return sum(map(lambda x: x[1] * expected_credits[x[0]], enumerate(grades))) / sum(expected_credits)


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
    idp_project_grades = get_best_fill(by_areas.get(Area.IDP, []), 11)
    idp_lecture_grades = get_best_fill(by_areas.get(Area.IDP_LECTURE, []), 5)
    idp_grades = idp_lecture_grades + idp_project_grades
    print("IDP", f"{avg_grade(idp_grades):.3f}", get_complete_str(idp_grades, 16))
    print_grades(idp_grades)
    idp_complete = get_complete(idp_grades, 16)

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
    major_name, major_grades = get_best_major(by_areas, areas)
    areas -= {major_name}
    print("major:", major_name, f"{avg_grade(major_grades):.3f}", get_complete_str(major_grades, 18))
    print_grades(major_grades)
    major_complete = get_complete(major_grades, 18)

    # 1st minor
    minor_1_name, minor_1_grades = get_best_minor(by_areas, areas)
    areas -= {minor_1_name}
    print("1st minor:", minor_1_name, f"{avg_grade(minor_1_grades):.3f}", get_complete_str(minor_1_grades, 8))
    print_grades(minor_1_grades)
    minor_1_complete = get_complete(minor_1_grades, 8)

    # 2nd minor
    minor_2_name, minor_2_grades = get_best_minor(by_areas, areas)
    areas -= {minor_2_name}
    print("2nd minor:", minor_2_name, f"{avg_grade(minor_2_grades):.3f}", get_complete_str(minor_2_grades, 8))
    print_grades(minor_2_grades)
    minor_2_complete = get_complete(minor_2_grades, 8)

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
    credits_needed = 19
    theo_credits_needed = 10 - sum_of_theo_credits(major_grades + minor_1_grades + minor_2_grades)
    free_choice_grades = get_free_choices(available_grades, credits_needed, theo_credits_needed)
    print("free choices:", f"{avg_grade(free_choice_grades):.3f}", get_complete_str(free_choice_grades, 19))
    print_grades(free_choice_grades)
    free_choices_complete = get_complete(free_choice_grades, 19)

    all_completions = [thesis_complete,
                       idp_complete,
                       sup_complete,
                       prac_complete,
                       seminar_complete,
                       major_complete,
                       minor_1_complete,
                       minor_2_complete,
                       free_choices_complete]

    all_grades = [thesis_grades,
                  idp_grades,
                  sup_grades,
                  prac_1_grades,
                  seminar_grades,
                  major_grades,
                  minor_1_grades,
                  minor_2_grades,
                  free_choice_grades]

    all_credit_weigths = [min(30, sum_of_credits(thesis_grades)),
                          min(16, sum_of_credits(idp_grades)),
                          min(6, sum_of_credits(sup_grades)),
                          min(10, sum_of_credits(prac_1_grades)),
                          min(5, sum_of_credits(seminar_grades)),
                          min(18, sum_of_credits(major_grades)),
                          min(8, sum_of_credits(minor_1_grades)),
                          min(8, sum_of_credits(minor_2_grades)),
                          min(19, sum_of_credits(free_choice_grades))]

    total_grade = get_reweight_grade(all_grades, all_credit_weigths)

    all_grades_flattened = flatten(all_grades)
    print("Masters Programm complete:", all(all_completions))
    print(f"theo credits reached: {sum_of_theo_credits(all_grades_flattened) > 10}: "
          f"{sum_of_theo_credits(all_grades_flattened)}/10")

    print(f"total grade: {total_grade:.3f}")


if __name__ == '__main__':
    print(f"Credit sum of all modules: {sum_of_credits(grades)}")
    compute_grade(grades)
