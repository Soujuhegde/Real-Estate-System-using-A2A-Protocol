"""
Deal Onboarding Agent — Business Logic
"""
import uuid
import json
import logging
from typing import List, Dict, Any
from shared.db import get_conn
from shared.llm import analyze_property_image

logger = logging.getLogger("deal_agent.handlers")

VALID_PROPERTY_TYPES = {
    "apartment", "villa", "plot", "commercial", "office",
    "warehouse", "studio", "penthouse", "row_house", "duplex",
}


def validate_property_input(data: Dict[str, Any]) -> List[str]:
    errors = []

    for field in ["title", "location", "property_type", "price"]:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # Price
    try:
        price = float(data["price"])
        if price <= 0:
            errors.append("price must be a positive number")
    except (ValueError, TypeError):
        errors.append("price must be a valid number")

    # Property type
    ptype = str(data.get("property_type", "")).lower()
    if ptype not in VALID_PROPERTY_TYPES:
        errors.append(
            f"property_type '{ptype}' is invalid. Valid types: {sorted(VALID_PROPERTY_TYPES)}"
        )

    # Optional numeric fields
    for field in ["area_sqft", "bedrooms", "bathrooms"]:
        val = data.get(field)
        if val is not None:
            try:
                if float(val) < 0:
                    errors.append(f"{field} must be non-negative")
            except (ValueError, TypeError):
                errors.append(f"{field} must be a valid number")

    # Location must be non-empty string
    if not str(data.get("location", "")).strip():
        errors.append("location must be a non-empty string")

    return errors


def onboard_property(data: Dict[str, Any]) -> str:
    """Persist property, return property_id. Deduplicate by title+location."""
    title = data["title"].strip()
    location = data["location"].strip()

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT property_id FROM properties WHERE title = ? AND location = ?",
            (title, location),
        ).fetchone()

        if existing:
            logger.info(f"Property already exists: {existing['property_id']}")
            return existing["property_id"]

        property_id = f"PROP-{str(uuid.uuid4())[:8].upper()}"
        
        # Base amenities
        user_amenities = data.get("amenities", [])
        if not isinstance(user_amenities, list):
            user_amenities = []
            
        ai_description = ""
        
        # Process Vision AI if image is provided
        if "image_base64" in data:
            vision_result = analyze_property_image(data["image_base64"])
            extracted = vision_result.get("extracted_amenities", [])
            ai_description = vision_result.get("marketing_description", "")
            
            # Merge amenities uniquely
            if isinstance(extracted, list):
                user_amenities = list(set(user_amenities + extracted))
                
            data["ai_description"] = ai_description
            
            # Remove base64 string before saving raw_json to save space
            del data["image_base64"]

        amenities_json = json.dumps(user_amenities)

        conn.execute(
            """INSERT INTO properties
               (property_id, title, location, property_type, price,
                area_sqft, bedrooms, bathrooms, amenities,
                owner_name, owner_contact, raw_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                property_id,
                title,
                location,
                data["property_type"].lower(),
                float(data["price"]),
                float(data.get("area_sqft") or 0),
                int(data.get("bedrooms") or 0),
                int(data.get("bathrooms") or 0),
                amenities_json,
                data.get("owner_name", ""),
                data.get("owner_contact", ""),
                json.dumps(data),
            ),
        )
        logger.info(f"New property onboarded: {property_id}")
        
        return property_id


def get_property(property_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM properties WHERE property_id = ?", (property_id,)
        ).fetchone()
        return dict(row) if row else {}
