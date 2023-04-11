from sequencing_runs.service_layer import unit_of_work


def instruments(uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = uow.session.execute(
            """
            SELECT instrument_id, type, model, status, timestamp_status_updated
            FROM instruments_illumina
            """
        )
        
        
    return results
