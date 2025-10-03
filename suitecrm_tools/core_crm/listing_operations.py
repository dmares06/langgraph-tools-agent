"""Listing creation and update operations."""

import json
from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def create_listing(
    title: str,
    address: str,
    asking_price: float,
    square_footage: int,
    zoning: str,
    year_built: str,
    parking_details: str,
    amenities: str,
    listing_type: str = "sale",
    status: str = "active",
    description: Optional[str] = None,
    contact_id: Optional[str] = None
) -> str:
    """
    Create a new listing.
    
    Args:
        title: Listing title (required)
        address: Listing address (required)
        asking_price: Asking price in dollars (required)
        square_footage: Listing size in square feet (required)
        listing_type: Listing type ('sale', 'lease', 'auction', 'foreclosure')
        status: Status ('active', 'inactive', 'LOI', 'under contract', 'sold')
        description: Listing description
        zoning: Zoning [ex: C-1, C-2, R-1, R-2, Commercial, OR-1, OR-2, M-1, M-2, etc.]
        year_built: Year built [ex: 1998, 2000, 2002, 2004]
        parking_details: Parking details (required)
        amenities: Amenities (required)
        contact_id: Associated contact/owner ID
    
    Returns:
        JSON string with created listing information
    """
    try:
        supabase = get_supabase_client()
        
        listing_data = {
            "title": title,
            "address": address,
            "asking_price": asking_price,
            "square_footage": square_footage,
            "listing_type": listing_type,
            "status": status,
            "zoning": zoning,
            "year_built": year_built,
            "parking_details": parking_details,
            "amenities": amenities,
            "description": description,
            "contact_id": contact_id,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("listings").insert(listing_data).execute()
        
        return json.dumps({
            "success": True,
            "listing": result.data[0],
            "message": f"Successfully created listing: {title} at {address}"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create listing: {str(e)}",
            "suggestion": "Verify all required fields are provided with correct types."
        })

@tool
def update_listing(
    listing_id: str,
    title: Optional[str] = None,
    asking_price: Optional[float] = None,
    status: Optional[str] = None,
    description: Optional[str] = None,
    square_footage: Optional[int] = None,
    zoning: Optional[str] = None,
    year_built: Optional[str] = None,
    parking_details: Optional[str] = None,
    amenities: Optional[str] = None
) -> str:
    """
    Update an existing listing.
    
    Args:
        listing_id: ID of the listing to update (required)
        title: Updated title
        asking_price: Updated asking price
        status: Updated status
        description: Updated description
        square_footage: Updated square footage
        zoning: Updated zoning
        year_built: Updated year built
        parking_details: Updated parking details
        amenities: Updated amenities
    Returns:
        JSON string with updated listing information
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {"updated_at": datetime.now().isoformat()}
        
        if title is not None:
            update_data["title"] = title
        if asking_price is not None:
            update_data["asking_price"] = asking_price
        if status is not None:
            update_data["status"] = status
        if description is not None:
            update_data["description"] = description
        if square_footage is not None:
            update_data["square_footage"] = square_footage
        if zoning is not None:
            update_data["zoning"] = zoning
        if year_built is not None:
            update_data["year_built"] = year_built
        if parking_details is not None:
            update_data["parking_details"] = parking_details
        if amenities is not None:
            update_data["amenities"] = amenities
        result = supabase.table("listings").update(update_data).eq("id", listing_id).execute()
        
        if not result.data:
            return json.dumps({
                "success": False,
                "error": f"Listing with ID {listing_id} not found"
            })
        
        return json.dumps({
            "success": True,
            "listing": result.data[0],
            "message": "Successfully updated listing"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update listing: {str(e)}"
        })