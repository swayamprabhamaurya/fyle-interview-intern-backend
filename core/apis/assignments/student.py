'''from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment

from .schema import AssignmentSchema, AssignmentSubmitSchema
student_assignments_resources = Blueprint('student_assignments_resources', __name__)


@student_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments"""
    students_assignments = Assignment.get_assignments_by_student(p.student_id)
    students_assignments_dump = AssignmentSchema().dump(students_assignments, many=True)
    return APIResponse.respond(data=students_assignments_dump)


@student_assignments_resources.route('/assignments', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def upsert_assignment(p, incoming_payload):
    """Create or Edit an assignment"""
    assignment = AssignmentSchema().load(incoming_payload)
    assignment.student_id = p.student_id

    upserted_assignment = Assignment.upsert(assignment)
    db.session.commit()
    upserted_assignment_dump = AssignmentSchema().dump(upserted_assignment)
    return APIResponse.respond(data=upserted_assignment_dump)


@student_assignments_resources.route('/assignments/submit', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def submit_assignment(p, incoming_payload):
    """Submit an assignment"""
    submit_assignment_payload = AssignmentSubmitSchema().load(incoming_payload)

    submitted_assignment = Assignment.submit(
        _id=submit_assignment_payload.id,
        teacher_id=submit_assignment_payload.teacher_id,
        auth_principal=p
    )
    db.session.commit()
    submitted_assignment_dump = AssignmentSchema().dump(submitted_assignment)
    return APIResponse.respond(data=submitted_assignment_dump)
'''
from flask import Blueprint, jsonify
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment
from core.libs.exceptions import FyleError
from core.models.assignments import AssignmentStateEnum
from .schema import AssignmentSchema, AssignmentSubmitSchema
student_assignments_resources = Blueprint('student_assignments_resources', __name__)
@student_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments"""
    students_assignments = Assignment.get_assignments_by_student(p.student_id)
    students_assignments_dump = AssignmentSchema().dump(students_assignments, many=True)
    return APIResponse.respond(data=students_assignments_dump)
@student_assignments_resources.route('/assignments', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def upsert_assignment(p, incoming_payload):
    """Create or Edit an assignment"""
    try:
        content = incoming_payload.get('content')
        if content is None:
            raise FyleError(400, "Content cannot be null")
        assignment_schema = AssignmentSchema()
        assignment = assignment_schema.load(incoming_payload)
        
        assignment.student_id = p.student_id
        upserted_assignment = Assignment.upsert(assignment)
        db.session.commit()
        upserted_assignment_dump = assignment_schema.dump(upserted_assignment)
        return APIResponse.respond(data=upserted_assignment_dump)
    except FyleError as e:
        return jsonify({
            'error': 'FyleError',
            'message': e.message,
        }), e.status_code
@student_assignments_resources.route('/assignments/submit', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def submit_assignment(p, incoming_payload):
    """Submit an assignment"""
    try:
        submit_assignment_payload = AssignmentSubmitSchema().load(incoming_payload)
        assignment_to_submit = Assignment.get_by_id(int(submit_assignment_payload.id))
        if assignment_to_submit.state != AssignmentStateEnum.DRAFT:
            raise FyleError(400, 'only a draft assignment can be submitted')
        submitted_assignment = Assignment.submit(
            _id=submit_assignment_payload.id,
            teacher_id=submit_assignment_payload.teacher_id,
            auth_principal=p
        )
        db.session.commit()
        submitted_assignment_dump = AssignmentSchema().dump(submitted_assignment)
        return APIResponse.respond(data=submitted_assignment_dump)
    except FyleError as e:
        return jsonify({
            'error': 'FyleError',
            'message': e.message,
        }), e.status_code
