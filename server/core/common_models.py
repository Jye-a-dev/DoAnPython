from flask_restx import Model, fields

message_model = Model("MessageResponse", {
    "message": fields.String(description="Status message"),
    "success": fields.Boolean(default=True)
})

count_model = Model("CountResponse", {
    "count": fields.Integer(description="Total matching entities count")
})

