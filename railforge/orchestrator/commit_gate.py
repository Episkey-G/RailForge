from railforge.core.models import AdapterResult, CommitGateResult, ContractSpec, QaFinding, QaReport, TaskItem


def build_commit_message(task: TaskItem, qa_report: QaReport) -> str:
    body = "\n".join("- %s" % item for item in task.done_definition[:3])
    return "feat(%s): %s\n\n%s\n- qa: %s" % (
        task.id,
        task.title.lower(),
        body,
        qa_report.status,
    )


def evaluate_commit_gate(workspace, task: TaskItem, contract: ContractSpec, qa_report: QaReport, implementation: AdapterResult, git_adapter) -> CommitGateResult:
    errors = []
    if qa_report.status != "approved":
        errors.append("qa_report_not_approved")
    if not contract.rollback:
        errors.append("missing_rollback")
    if not contract.verification:
        errors.append("missing_verification")
    for changed_file in implementation.changed_files:
        if not any(changed_file.startswith(prefix) for prefix in contract.allowed_paths):
            errors.append("out_of_scope:%s" % changed_file)

    message = build_commit_message(task, qa_report)
    if errors:
        return CommitGateResult(
            passed=False,
            message=message,
            dry_run=True,
            details={"errors": errors},
        )

    return git_adapter.create_commit(workspace, message, implementation.changed_files)

