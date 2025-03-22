from utils.constants import STAGE


class URL:
    CUSTOMER_AUTH = f'https://api2-{STAGE}.jiffy-team.com/customer/sms/verify'
    CREATE_ORDER = f'https://api2-{STAGE}.jiffy-team.com/orders/v2/orders/new'
    COURIERS_INFO = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/info'
    USER_AUTH = f'https://api2-{STAGE}.jiffy-team.com/auth/v1/auth/otp/confirm'
    MARK_ONLINE = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/mark-online'
    MARK_ARRIVAL = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/mark-arrival'
    TASK_ON_POINT = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/on-point'
    TASK_START = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/start'
    TASK_COMPLETE = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/complete'
    UPLOAD_PHOTO = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/upload-photo'
    JOB_ACCEPT = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/jobs/accept'
    COURIER_MARK_RETURNING = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/mark-returning'
    JOBS_GET_ASSIGNED = f'https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/jobs/get-assigned'