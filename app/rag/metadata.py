from pathlib import Path


def build_metadata(filename: str) -> dict:
    """
    Build metadata describing the document.

    This metadata will later be attached to every chunk
    before it enters the vector database.
    """

    name = Path(filename).stem.lower()

    metadata = {
        "source": filename,
        "document_type": "unknown",
        "authority": "unknown",
        "version": None,
        "account_id": None,
    }

    # --------------------------------------------------------
    # Support policies
    # --------------------------------------------------------

    if "support_policy_v3" in name:
        metadata.update(
            {
                "document_type": "support_policy",
                "authority": "current",
                "version": "v3",
            }
        )

    elif "support_policy_v2" in name:
        metadata.update(
            {
                "document_type": "support_policy",
                "authority": "deprecated",
                "version": "v2",
            }
        )

    # --------------------------------------------------------
    # SOP
    # --------------------------------------------------------

    elif "cancellation_and_service_credit_sop_v4" in name:
        metadata.update(
            {
                "document_type": "cancellation_service_credit_sop",
                "authority": "current",
                "version": "v4",
            }
        )

    # --------------------------------------------------------
    # Product knowledge
    # --------------------------------------------------------

    elif "product_operations_guide" in name:
        metadata.update(
            {
                "document_type": "product_operations",
                "authority": "current",
            }
        )

    # --------------------------------------------------------
    # Customer contracts
    # --------------------------------------------------------

    elif "northstar_logistics" in name:
        metadata.update(
            {
                "document_type": "customer_contract",
                "authority": "contract",
                "account_id": "ACCT-001",
            }
        )

    elif "lumenworks" in name:
        metadata.update(
            {
                "document_type": "customer_contract",
                "authority": "contract",
                "account_id": "ACCT-002",
            }
        )

    return metadata