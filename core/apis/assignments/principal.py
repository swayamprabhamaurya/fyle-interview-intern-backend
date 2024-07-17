'''from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment



from sqlalchemy import or_
from models.assignments import Assignment  # Adjust this based on your actual model
from flask import Blueprint, request, jsonify
from models.assignments import Assignment  # Import your SQLAlchemy Assignment model here
from sqlalchemy.orm.exc import NoResultFound


principal_assignments_resources = Blueprint('principal_assignments_resources', __name__)


@principal_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)

def get_principal_assignments():
    # Assuming Assignment is your SQLAlchemy model for assignments
    assignments = Assignment.query.filter(or_(Assignment.state == 'SUBMITTED', Assignment.state == 'GRADED')).all()
    
    # Serialize assignments to JSON format
    assignments_list = []
    for assignment in assignments:
        assignments_list.append({
            'id': assignment.id,
            'content': assignment.content,
            'created_at': assignment.created_at.isoformat(),
            'updated_at': assignment.updated_at.isoformat(),
            'state': assignment.state,
            'student_id': assignment.student_id,
            'teacher_id': assignment.teacher_id,
            'grade': assignment.grade
        })
    
    return jsonify({'data': assignments_list}), 200


@principal_assignments_resources.route('/assignments/grade', methods=['POST'])
def grade_or_regrade_assignment():
    data = request.get_json()
    assignment_id = data.get('id')
    grade = data.get('grade')

    # Validate payload
    if not assignment_id or not grade:
        return jsonify({"error": "Missing assignment ID or grade"}), 400
    
    # Query the assignment by ID
    try:
        assignment = Assignment.query.filter_by(id=assignment_id).one()
    except NoResultFound:
        return jsonify({"error": "Assignment not found"}), 404

    # Update assignment grade and state
    assignment.grade = grade
    assignment.state = "GRADED"  # Assuming state transitions are managed elsewhere if needed

    # Commit changes to the database
    db.session.commit()

    # Return updated assignment details
    return jsonify({
        "data": {
            "id": assignment.id,
            "content": assignment.content,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
            "grade": assignment.grade,
            "state": assignment.state,
            "student_id": assignment.student_id,
            "teacher_id": assignment.teacher_id
        }
    }), 200
    
'''

from flask import Blueprint, jsonify
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment
from core.models.assignments import AssignmentStateEnum
from core.libs.exceptions import FyleError

from .schema import AssignmentSchema, AssignmentGradeSchema
principal_assignments_resources = Blueprint('principal_assignments_resources', __name__)


@principal_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments"""
    principal_assignments = Assignment.get_assignments_by_principal(p.principal_id)
    principal_assignments_dump = AssignmentSchema().dump(principal_assignments, many=True)
    return APIResponse.respond(data=principal_assignments_dump)


@principal_assignments_resources.route('/assignments/grade', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def grade_or_regrade_assignment(p, incoming_payload):
    """Grade or re-grade an assignment"""
    grade_assignment_payload = AssignmentGradeSchema().load(incoming_payload)

    assignment = Assignment.get_by_id(int(grade_assignment_payload.id))
    
    try:
        if assignment.state == AssignmentStateEnum.DRAFT:
            raise FyleError(400, "Cannot grade an assignment in the 'Draft' state")

        graded_assignment = Assignment.mark_grade(
            _id=grade_assignment_payload.id,
            grade=grade_assignment_payload.grade,
            auth_principal=p
        )

        db.session.commit()
        graded_assignment_dump = AssignmentSchema().dump(graded_assignment)
        return APIResponse.respond(data=graded_assignment_dump)

    except FyleError as e:
        return jsonify({
            'error': 'FyleError',
            'message': e.message,
        }), e.status_code
