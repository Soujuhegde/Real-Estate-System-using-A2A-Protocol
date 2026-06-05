"""
Customer Onboarding Agent — Business Logic
"""
import uuid
import json
import re
import logging
from typing import List, Dict, Any
from shared.db import get_conn

logger = logging.getLogger("customer_agent.handlers")


def validate_customer_input(data: Dict[str, Any]) -> List[str]:
    """Returns list of validation error messages (empty = valid)"""
    errors = []

    # Required fields
    for field in ["full_name", "email", "buyer_type", "budget_min", "budget_max"]:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors  # stop early if core fields missing

    # Email format
    email = data.get("email", "")
    if not re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email):
        errors.append(f"Invalid email format: {email}")

    # Buyer type
    valid_types = {"buyer", "investor", "both"}
    if data.get("buyer_type", "").lower() not in valid_types:
        errors.append(f"buyer_type must be one of {valid_types}")

    # Budget ranges
    try:
        bmin = float(data["budget_min"])
        bmax = float(data["budget_max"])
        if bmin < 0:
            errors.append("budget_min must be non-negative")
        if bmax < bmin:
            errors.append("budget_max must be >= budget_min")
        if bmax == 0:
            errors.append("budget_max must be greater than 0")
    except (ValueError, TypeError):
        errors.append("budget_min and budget_max must be valid numbers")

    return errors


def onboard_customer(data: Dict[str, Any]) -> str:
    """Persist customer to DB, return customer_id"""
    # Check for duplicate email
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT customer_id FROM customers WHERE email = ?",
            (data["email"].lower().strip(),),
        ).fetchone()

        if existing:
            logger.info(f"Customer already exists for email {data['email']}, returning existing ID")
            return existing["customer_id"]

        customer_id = f"CUST-{str(uuid.uuid4())[:8].upper()}"
        preferred = (
            json.dumps(data["preferred_locations"])
            if isinstance(data.get("preferred_locations"), list)
            else data.get("preferred_locations", "[]")
        )

        conn.execute(
            """INSERT INTO customers
               (customer_id, full_name, email, phone, buyer_type,
                budget_min, budget_max, preferred_locations, raw_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                customer_id,
                data["full_name"].strip(),
                data["email"].lower().strip(),
                data.get("phone", ""),
                data["buyer_type"].lower(),
                float(data["budget_min"]),
                float(data["budget_max"]),
                preferred,
                json.dumps(data),
            ),
        )
        logger.info(f"Onboarded new customer: {customer_id}")
        return customer_id


def get_customer(customer_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        return dict(row) if row else {}
