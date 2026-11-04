"""Preserve assistant review separately; never manufacture human annotations."""
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent/"results"
# Notes were written after reading the selected answers and all retrieved chunks.
NOTES=[
("The answer quotes an emergency WFH rule but exposes SOURCE/PAGE labels and points to chunk 2, which starts partway through that rule.","citation_traceability",2),
("The five-day carry-forward answer is supported by leave-policy.txt but has no numbered inline citation.","citation_traceability",2),
("The twenty-day annual allowance is supported, but the answer exposes the internal SOURCE label.","citation_traceability",1),
("The workout-clothes answer has supporting evidence and a numbered citation, but calls PDF page 12 a section number without evidence.","citation_traceability",1),
("The dating answer omits the retrieved restriction on dating direct reports and has no numbered citation.","incomplete_conditions",3),
("The direct-report dating prohibition is supported, but the answer gives only a filename and page rather than an inline context citation.","citation_traceability",2),
("The five-day carry-forward maximum is supported, but SOURCE is exposed in the answer.","citation_traceability",1),
("The reporting-manager answer is supported by the leave policy, but contains no numbered citation.","citation_traceability",2),
("The answer abstains even though retrieved page 18 says visitors must be kept away from dangerous and sensitive areas; a qualified answer was possible.","false_abstention",3),
("The emergency-leave answer includes same-day timing and the reporting manager, but leaks SOURCE and PAGE formatting.","citation_traceability",1),
("The answer assigns the ten-hour cap to non-exempt employees, while the retrieved template assigns it to exempt employees; the template status is also undisclosed.","wrong_scope_or_contact",4),
("Shredding is supported on page 7, but the answer lacks the numbered citation required for inspection.","citation_traceability",2),
("The answer presents bracketed PTO template values as company policy and leaks SOURCE/PAGE labels without flagging that approval is unknown.","unresolved_template",4),
("The dental-premium question correctly abstains because the retrieved insurance text does not specify a premium.","correct_abstention",0),
("The commuter-rail question correctly abstains because the retrieved texts do not specify such a subsidy.","correct_abstention",0),
("The answer sends a manager-involved harassment complaint back to the manager even though retrieved page 9 explicitly directs that situation to HR.","wrong_scope_or_contact",5),
("Keeping receipts is supported, but the answer contains no numbered citation.","citation_traceability",2),
("The answer silently chooses two of three unresolved visitor-approver template roles and exposes SOURCE/PAGE labels.","unresolved_template",4),
("The overtime answer omits the retrieved supervisor-authorization condition and the template's jurisdiction condition; it also lacks numbered citations.","incomplete_conditions",3),
("The parking-fee answer correctly declines to invent a fee but adds text after the required exact abstention sentence.","abstention_format",1)
]


def main():
    data=json.loads((OUT/"week5_sample.json").read_text(encoding="utf-8"))
    data["reviewer"]="AI assistant review; not a human-labelled submission"
    for row,(note,group,severity) in zip(data["traces"],NOTES):
        row.update(open_note=note,problem_type=group,severity=severity,human_pass=None)
    (OUT/"week5_assistant_review.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    from course.run import rank_notes
    rank_notes(OUT/"week5_assistant_review.json")


if __name__=="__main__":
    main()
