from datetime import date, datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class BaseOut(BaseModel):
    id: str
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, extra="ignore")


T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# 1. EV_USER
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None

    @model_validator(mode="after")
    def assemble_names(self):
        if not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        elif self.full_name and not self.first_name:
            parts = self.full_name.split(" ", 1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else ""
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseOut):
    user_id: Optional[int | str] = None
    email: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    role: str = "customer"
    status: str = "active"
    phone: Optional[str] = None
    created_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# 2. ADMIN
# ---------------------------------------------------------------------------
class AdminBase(BaseModel):
    email: EmailStr
    admin_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_no: Optional[str] = None
    phone: Optional[str] = None
    role: str = "ADMIN"
    experience: int = Field(default=0, ge=0)
    privileges: list[str] = Field(default_factory=lambda: ["manage_users", "manage_stations", "manage_tariffs"])
    user_id: Optional[str] = None

    @model_validator(mode="after")
    def unify_admin_names(self):
        if not self.full_name and self.admin_name:
            self.full_name = self.admin_name
        elif not self.admin_name and self.full_name:
            self.admin_name = self.full_name
        if not self.phone_no and self.phone:
            self.phone_no = self.phone
        elif not self.phone and self.phone_no:
            self.phone = self.phone_no
        return self


class AdminCreate(AdminBase):
    password: Optional[str] = "AdminPass123!"


class AdminUpdate(BaseModel):
    admin_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_no: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    experience: Optional[int] = Field(default=None, ge=0)
    privileges: Optional[list[str]] = None
    password: Optional[str] = None
    status: Optional[str] = None


class AdminOut(BaseOut):
    admin_id: Optional[int | str] = None
    user_id: Optional[str] = None
    email: str
    admin_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_no: Optional[str] = None
    phone: Optional[str] = None
    role: str = "ADMIN"
    experience: int = 0
    privileges: list[str] = Field(default_factory=list)
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 3. TARIFF
# ---------------------------------------------------------------------------
class TariffBase(BaseModel):
    tariff_name: Optional[str] = None
    name: Optional[str] = None
    rate_per_kwh: Optional[float] = Field(default=None, ge=0)
    price_per_kwh: Optional[float] = Field(default=None, ge=0)
    peak_hour_rate: Optional[float] = Field(default=0.0, ge=0)
    off_peak_rate: Optional[float] = Field(default=0.0, ge=0)
    valid_from: Optional[datetime] = None
    start_date: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    is_active: bool = True
    status: Optional[str] = "ACTIVE"

    @model_validator(mode="after")
    def unify_tariff_fields(self):
        if not self.name and self.tariff_name:
            self.name = self.tariff_name
        elif not self.tariff_name and self.name:
            self.tariff_name = self.name

        if self.price_per_kwh is None and self.rate_per_kwh is not None:
            self.price_per_kwh = self.rate_per_kwh
        elif self.rate_per_kwh is None and self.price_per_kwh is not None:
            self.rate_per_kwh = self.price_per_kwh
        elif self.price_per_kwh is None and self.rate_per_kwh is None:
            self.price_per_kwh = 10.0
            self.rate_per_kwh = 10.0

        if not self.valid_from and self.start_date:
            self.valid_from = self.start_date
        elif not self.start_date and self.valid_from:
            self.start_date = self.valid_from
        elif not self.valid_from and not self.start_date:
            from datetime import timezone
            now_dt = datetime.now(timezone.utc)
            self.valid_from = now_dt
            self.start_date = now_dt
        return self


class TariffCreate(TariffBase):
    pass


class TariffUpdate(BaseModel):
    tariff_name: Optional[str] = None
    name: Optional[str] = None
    rate_per_kwh: Optional[float] = Field(default=None, ge=0)
    price_per_kwh: Optional[float] = Field(default=None, ge=0)
    peak_hour_rate: Optional[float] = Field(default=None, ge=0)
    off_peak_rate: Optional[float] = Field(default=None, ge=0)
    valid_from: Optional[datetime] = None
    start_date: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None


class TariffOut(BaseOut):
    tariff_id: Optional[int | str] = None
    name: str
    tariff_name: Optional[str] = None
    price_per_kwh: float
    rate_per_kwh: Optional[float] = None
    peak_hour_rate: Optional[float] = 0.0
    off_peak_rate: Optional[float] = 0.0
    valid_from: Optional[datetime] = None
    start_date: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    is_active: bool = True
    status: Optional[str] = "ACTIVE"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 4. SOURCE
# ---------------------------------------------------------------------------
class SourceBase(BaseModel):
    source_name: Optional[str] = None
    name: Optional[str] = None
    source_type: str = "RENEWABLE"  # RENEWABLE or NON_RENEWABLE
    capacity: Optional[float] = Field(default=None, ge=0)
    capacity_kw: Optional[float] = Field(default=None, ge=0)
    unit: Optional[str] = "kW"
    status: str = "ACTIVE"
    energy_generated_kwh: float = 0.0
    description: Optional[str] = None

    @model_validator(mode="after")
    def unify_source_fields(self):
        if not self.name and self.source_name:
            self.name = self.source_name
        elif not self.source_name and self.name:
            self.source_name = self.name
        if self.capacity_kw is None and self.capacity is not None:
            self.capacity_kw = self.capacity
        elif self.capacity is None and self.capacity_kw is not None:
            self.capacity = self.capacity_kw
        elif self.capacity is None and self.capacity_kw is None:
            self.capacity = 1000.0
            self.capacity_kw = 1000.0
        return self


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    source_name: Optional[str] = None
    name: Optional[str] = None
    source_type: Optional[str] = None
    capacity: Optional[float] = Field(default=None, ge=0)
    capacity_kw: Optional[float] = Field(default=None, ge=0)
    unit: Optional[str] = None
    status: Optional[str] = None
    energy_generated_kwh: Optional[float] = None
    description: Optional[str] = None


class SourceOut(BaseOut):
    source_id: Optional[int | str] = None
    name: str
    source_name: Optional[str] = None
    source_type: str
    capacity: Optional[float] = None
    capacity_kw: float
    unit: Optional[str] = "kW"
    status: str = "ACTIVE"
    energy_generated_kwh: float = 0.0
    description: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 5. CHARGING_STATION
# ---------------------------------------------------------------------------
class StationBase(BaseModel):
    station_name: Optional[str] = None
    name: Optional[str] = None
    station_code: Optional[str] = None
    address: str
    city: Optional[str] = "Metroville"
    latitude: float
    longitude: float
    operating_hours: Optional[str] = "24/7"
    grid_id: Optional[str] = None
    status: str = "operational"
    total_ports: Optional[int] = 0

    @model_validator(mode="after")
    def unify_station_fields(self):
        if not self.name and self.station_name:
            self.name = self.station_name
        elif not self.station_name and self.name:
            self.station_name = self.name
        if not self.station_code:
            self.station_code = f"STN-{(self.name or 'GEN')[:3].upper()}"
        return self


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    station_name: Optional[str] = None
    name: Optional[str] = None
    station_code: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    operating_hours: Optional[str] = None
    grid_id: Optional[str] = None
    status: Optional[str] = None
    total_ports: Optional[int] = None


class StationOut(BaseOut):
    station_id: Optional[int | str] = None
    name: str
    station_name: Optional[str] = None
    station_code: str
    address: str
    city: Optional[str] = None
    latitude: float
    longitude: float
    operating_hours: Optional[str] = None
    grid_id: Optional[str] = None
    status: str
    total_ports: Optional[int] = 0
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 6. EV
# ---------------------------------------------------------------------------
class EVBase(BaseModel):
    vehicle_number: Optional[str] = None
    registration_number: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    model: str
    battery_capacity: Optional[float] = Field(default=None, gt=0)
    battery_capacity_kwh: Optional[float] = Field(default=None, gt=0)
    battery_capacity_kw: Optional[float] = Field(default=None, gt=0)
    connector_type: str = "CCS"
    manufacturing_year: Optional[int] = None
    manufacture_year: Optional[int] = None
    is_active: bool = True
    status: Optional[str] = "ACTIVE"
    user_id: Optional[str] = None
    owner_id: Optional[str] = None

    @model_validator(mode="after")
    def unify_ev_fields(self):
        if not self.registration_number and self.vehicle_number:
            self.registration_number = self.vehicle_number
        elif not self.vehicle_number and self.registration_number:
            self.vehicle_number = self.registration_number

        if not self.brand and self.manufacturer:
            self.brand = self.manufacturer
        elif not self.manufacturer and self.brand:
            self.manufacturer = self.brand

        cap = self.battery_capacity or self.battery_capacity_kwh or self.battery_capacity_kw or 60.0
        self.battery_capacity = cap
        self.battery_capacity_kwh = cap
        self.battery_capacity_kw = cap

        if not self.manufacturing_year and self.manufacture_year:
            self.manufacturing_year = self.manufacture_year
        elif not self.manufacture_year and self.manufacturing_year:
            self.manufacture_year = self.manufacturing_year

        if not self.owner_id and self.user_id:
            self.owner_id = self.user_id
        elif not self.user_id and self.owner_id:
            self.user_id = self.owner_id
        return self


class EVCreate(EVBase):
    pass


class EVUpdate(BaseModel):
    vehicle_number: Optional[str] = None
    registration_number: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    battery_capacity: Optional[float] = Field(default=None, gt=0)
    battery_capacity_kwh: Optional[float] = Field(default=None, gt=0)
    connector_type: Optional[str] = None
    manufacturing_year: Optional[int] = None
    manufacture_year: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    user_id: Optional[str] = None
    owner_id: Optional[str] = None


class EVOut(BaseOut):
    ev_id: Optional[int | str] = None
    owner_id: Optional[str] = None
    user_id: Optional[str] = None
    model: str
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    registration_number: str
    vehicle_number: Optional[str] = None
    battery_capacity_kwh: float
    battery_capacity: Optional[float] = None
    connector_type: str
    manufacturing_year: Optional[int] = None
    manufacture_year: Optional[int] = None
    is_active: bool = True
    status: Optional[str] = "ACTIVE"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 7. USER_PHONE
# ---------------------------------------------------------------------------
class UserPhoneBase(BaseModel):
    user_id: Optional[str] = None
    phone_no: Optional[str] = None
    number: Optional[str] = None
    phone_type: Optional[str] = None
    label: Optional[str] = None
    is_primary: bool = False

    @model_validator(mode="after")
    def unify_phone_fields(self):
        if not self.number and self.phone_no:
            self.number = self.phone_no
        elif not self.phone_no and self.number:
            self.phone_no = self.number
        if not self.label and self.phone_type:
            self.label = self.phone_type
        elif not self.phone_type and self.label:
            self.phone_type = self.label
        return self


class UserPhoneCreate(UserPhoneBase):
    pass


class UserPhoneUpdate(BaseModel):
    phone_no: Optional[str] = None
    number: Optional[str] = None
    phone_type: Optional[str] = None
    label: Optional[str] = None
    is_primary: Optional[bool] = None


class UserPhoneOut(BaseOut):
    user_id: str
    number: str
    phone_no: Optional[str] = None
    label: Optional[str] = None
    phone_type: Optional[str] = None
    is_primary: bool = False
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 8. GRID
# ---------------------------------------------------------------------------
class GridBase(BaseModel):
    grid_name: Optional[str] = None
    name: Optional[str] = None
    voltage_level: Optional[str] = "400kV"
    capacity: Optional[float] = Field(default=None, ge=0)
    capacity_kw: Optional[float] = Field(default=None, ge=0)
    current_load: Optional[float] = 0.0
    current_load_kw: Optional[float] = 0.0
    location: Optional[str] = None
    status: str = "ACTIVE"
    source_id: Optional[str] = None

    @model_validator(mode="after")
    def unify_grid_fields(self):
        if not self.name and self.grid_name:
            self.name = self.grid_name
        elif not self.grid_name and self.name:
            self.grid_name = self.name
        if self.capacity_kw is None and self.capacity is not None:
            self.capacity_kw = self.capacity
        elif self.capacity is None and self.capacity_kw is not None:
            self.capacity = self.capacity_kw
        elif self.capacity is None and self.capacity_kw is None:
            self.capacity = 50000.0
            self.capacity_kw = 50000.0

        if self.current_load_kw is None and self.current_load is not None:
            self.current_load_kw = self.current_load
        elif self.current_load is None and self.current_load_kw is not None:
            self.current_load = self.current_load_kw
        return self


class GridCreate(GridBase):
    pass


class GridUpdate(BaseModel):
    grid_name: Optional[str] = None
    name: Optional[str] = None
    voltage_level: Optional[str] = None
    capacity: Optional[float] = Field(default=None, ge=0)
    capacity_kw: Optional[float] = Field(default=None, ge=0)
    current_load: Optional[float] = None
    current_load_kw: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
    source_id: Optional[str] = None


class GridOut(BaseOut):
    grid_id: Optional[int | str] = None
    name: str
    grid_name: Optional[str] = None
    voltage_level: Optional[str] = None
    capacity_kw: float
    capacity: Optional[float] = None
    current_load_kw: float = 0.0
    current_load: Optional[float] = 0.0
    location: Optional[str] = None
    status: str = "ACTIVE"
    source_id: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 9. CHARGING_PORT
# ---------------------------------------------------------------------------
class PortBase(BaseModel):
    station_id: str
    station_code: Optional[str] = None
    port_number: int = Field(ge=1)
    charger_type: Optional[str] = None  # AC or DC_FAST
    connector_type: Optional[str] = None  # Type 2, CCS, CHAdeMO
    power_output: Optional[float] = Field(default=None, gt=0)
    rated_power_kw: Optional[float] = Field(default=None, gt=0)
    availability_status: Optional[str] = None  # AVAILABLE, OCCUPIED, MAINTENANCE, OUT_OF_ORDER
    status: Optional[str] = None  # operational, maintenance, offline
    tariff_id: Optional[str] = None

    @model_validator(mode="after")
    def unify_port_fields(self):
        if not self.connector_type and self.charger_type:
            self.connector_type = self.charger_type
        elif not self.charger_type and self.connector_type:
            self.charger_type = "DC_FAST" if "DC" in self.connector_type.upper() or "CCS" in self.connector_type.upper() else "AC"

        if self.rated_power_kw is None and self.power_output is not None:
            self.rated_power_kw = self.power_output
        elif self.power_output is None and self.rated_power_kw is not None:
            self.power_output = self.rated_power_kw
        elif self.rated_power_kw is None and self.power_output is None:
            self.rated_power_kw = 50.0
            self.power_output = 50.0

        if not self.status and self.availability_status:
            self.status = "operational" if self.availability_status == "AVAILABLE" else "maintenance"
        elif not self.availability_status and self.status:
            self.availability_status = "AVAILABLE" if self.status == "operational" else "MAINTENANCE"
        elif not self.status and not self.availability_status:
            self.status = "operational"
            self.availability_status = "AVAILABLE"
        return self


class PortCreate(PortBase):
    pass


class PortUpdate(BaseModel):
    charger_type: Optional[str] = None
    connector_type: Optional[str] = None
    power_output: Optional[float] = Field(default=None, gt=0)
    rated_power_kw: Optional[float] = Field(default=None, gt=0)
    availability_status: Optional[str] = None
    status: Optional[str] = None
    tariff_id: Optional[str] = None


class PortOut(BaseOut):
    port_id: Optional[int | str] = None
    station_id: str
    station_code: Optional[str] = None
    port_number: int
    charger_type: Optional[str] = None
    connector_type: str
    power_output: Optional[float] = None
    rated_power_kw: float
    availability_status: Optional[str] = None
    status: str
    tariff_id: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 10. AC_PORT
# ---------------------------------------------------------------------------
class ACPortBase(BaseModel):
    station_id: str
    port_number: int = Field(ge=1)
    port_id: Optional[str] = None
    connector_standard: str = "TYPE_2"
    ac_phase: str = "SINGLE"  # SINGLE or THREE
    ac_power_kw: Optional[float] = Field(default=None, gt=0)
    voltage: Optional[float] = 230.0
    current: Optional[float] = 32.0


class ACPortCreate(ACPortBase):
    pass


class ACPortUpdate(BaseModel):
    connector_standard: Optional[str] = None
    ac_phase: Optional[str] = None
    ac_power_kw: Optional[float] = Field(default=None, gt=0)
    voltage: Optional[float] = None
    current: Optional[float] = None


class ACPortOut(BaseOut):
    port_id: Optional[str] = None
    station_id: str
    port_number: int
    connector_standard: str
    ac_phase: str
    ac_power_kw: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 11. DC_FAST_PORT
# ---------------------------------------------------------------------------
class DCFastPortBase(BaseModel):
    station_id: str
    port_number: int = Field(ge=1)
    port_id: Optional[str] = None
    dc_voltage: float = Field(gt=0, default=400.0)
    maximum_current: float = Field(gt=0, default=125.0)
    dc_power_kw: Optional[float] = Field(default=None, gt=0)
    supported_standard: Optional[str] = "CCS2"


class DCFastPortCreate(DCFastPortBase):
    pass


class DCFastPortUpdate(BaseModel):
    dc_voltage: Optional[float] = Field(default=None, gt=0)
    maximum_current: Optional[float] = Field(default=None, gt=0)
    dc_power_kw: Optional[float] = Field(default=None, gt=0)
    supported_standard: Optional[str] = None


class DCFastPortOut(BaseOut):
    port_id: Optional[str] = None
    station_id: str
    port_number: int
    dc_voltage: float
    maximum_current: float
    dc_power_kw: Optional[float] = None
    supported_standard: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 12. BOOKING
# ---------------------------------------------------------------------------
class BookingBase(BaseModel):
    ev_id: str
    station_id: str
    port_id: str
    port_number: Optional[int] = None
    booking_date: Optional[str] = None
    booking_time: Optional[datetime] = None
    start_time: datetime
    end_time: datetime
    status: Optional[str] = "pending"
    booking_status: Optional[str] = None

    @model_validator(mode="after")
    def unify_booking_status(self):
        if not self.booking_status and self.status:
            self.booking_status = self.status.upper()
        elif not self.status and self.booking_status:
            self.status = self.booking_status.lower()
        return self


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    status: Optional[str] = None
    booking_status: Optional[str] = None


class BookingOut(BaseOut):
    booking_id: Optional[int | str] = None
    user_id: str
    ev_id: str
    station_id: str
    port_id: str
    port_number: Optional[int] = None
    booking_date: Optional[str] = None
    booking_time: Optional[datetime] = None
    start_time: datetime
    end_time: datetime
    status: str
    booking_status: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 13. CHARGING_SESSION
# ---------------------------------------------------------------------------
class SessionStart(BaseModel):
    booking_id: Optional[str] = None
    port_id: str
    ev_id: Optional[str] = None


class SessionEnd(BaseModel):
    energy_delivered_kwh: Optional[float] = Field(default=None, ge=0)
    energy_consumed: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def unify_energy(self):
        if self.energy_delivered_kwh is None and self.energy_consumed is not None:
            self.energy_delivered_kwh = self.energy_consumed
        elif self.energy_consumed is None and self.energy_delivered_kwh is not None:
            self.energy_consumed = self.energy_delivered_kwh
        elif self.energy_delivered_kwh is None and self.energy_consumed is None:
            self.energy_delivered_kwh = 10.0
            self.energy_consumed = 10.0
        return self


class SessionOut(BaseOut):
    session_id: Optional[int | str] = None
    booking_id: Optional[str] = None
    user_id: str
    ev_id: Optional[str] = None
    port_id: str
    started_at: datetime
    start_time: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    end_time: Optional[datetime] = None
    energy_delivered_kwh: Optional[float] = None
    energy_consumed: Optional[float] = None
    energy_consumed_kwh: Optional[float] = None
    total_amount: Optional[float] = None
    tariff_price_per_kwh: Optional[float] = None
    status: str
    session_status: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 14. PAYMENT
# ---------------------------------------------------------------------------
class PaymentBase(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    amount: float = Field(ge=0)
    payment_method: Optional[str] = "simulated"
    payment_mode: Optional[str] = "UPI"
    payment_date: Optional[str] = None
    transaction_reference: Optional[str] = None
    status: Optional[str] = "completed"
    payment_status: Optional[str] = None

    @model_validator(mode="after")
    def unify_payment_fields(self):
        if not self.payment_mode and self.payment_method:
            self.payment_mode = self.payment_method.upper()
        elif not self.payment_method and self.payment_mode:
            self.payment_method = self.payment_mode.lower()

        if not self.payment_status and self.status:
            self.payment_status = self.status.upper()
        elif not self.status and self.payment_status:
            self.status = self.payment_status.lower()
        return self


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None


class PaymentOut(BaseOut):
    payment_id: Optional[int | str] = None
    session_id: str
    user_id: str
    amount: float
    payment_method: str = "simulated"
    payment_mode: Optional[str] = None
    payment_date: Optional[str] = None
    transaction_reference: str
    status: str
    payment_status: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 15. SCHEDULE
# ---------------------------------------------------------------------------
class ScheduleBase(BaseModel):
    station_id: str
    port_id: Optional[str] = None
    schedule_date: Optional[str] = None
    start_time: datetime
    end_time: datetime
    available_slots: int = Field(default=10, ge=0)
    schedule_type: Optional[str] = "REGULAR"
    is_available: bool = True
    status: Optional[str] = "ACTIVE"
    description: Optional[str] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def unify_schedule_fields(self):
        if not self.note and self.description:
            self.note = self.description
        elif not self.description and self.note:
            self.description = self.note
        return self


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    station_id: Optional[str] = None
    port_id: Optional[str] = None
    schedule_date: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    available_slots: Optional[int] = Field(default=None, ge=0)
    schedule_type: Optional[str] = None
    is_available: Optional[bool] = None
    status: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None


class ScheduleOut(BaseOut):
    schedule_id: Optional[int | str] = None
    station_id: str
    port_id: Optional[str] = None
    schedule_date: Optional[str] = None
    start_time: datetime
    end_time: datetime
    available_slots: int = 10
    schedule_type: Optional[str] = None
    is_available: bool = True
    status: Optional[str] = "ACTIVE"
    description: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 16. MAINTENANCE
# ---------------------------------------------------------------------------
class MaintenanceBase(BaseModel):
    station_id: Optional[str] = None
    port_id: Optional[str] = None
    admin_id: Optional[str] = None
    maintenance_type: str = "PREVENTIVE"  # PREVENTIVE or CORRECTIVE
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    maintenance_date: Optional[str] = None
    completion_date: Optional[datetime] = None
    cost: float = Field(default=0.0, ge=0)
    status: str = "planned"

    @model_validator(mode="after")
    def unify_maintenance_fields(self):
        if not self.title and self.description:
            self.title = (self.description[:40] + "...") if len(self.description) > 40 else self.description
        elif not self.description and self.title:
            self.description = self.title
        return self


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    station_id: Optional[str] = None
    port_id: Optional[str] = None
    admin_id: Optional[str] = None
    maintenance_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    maintenance_date: Optional[str] = None
    completion_date: Optional[datetime] = None
    cost: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None


class MaintenanceOut(BaseOut):
    maintenance_id: Optional[int | str] = None
    station_id: Optional[str] = None
    port_id: Optional[str] = None
    admin_id: Optional[str] = None
    maintenance_type: str = "PREVENTIVE"
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    maintenance_date: Optional[str] = None
    completion_date: Optional[datetime] = None
    cost: float = 0.0
    status: str
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 17. NOTIFICATION
# ---------------------------------------------------------------------------
class NotificationBase(BaseModel):
    user_id: str
    message: str
    notification_type: Optional[str] = "INFO"
    read_status: Optional[str] = "UNREAD"
    is_read: bool = False
    sent_date: Optional[datetime] = None

    @model_validator(mode="after")
    def unify_notification_fields(self):
        if self.read_status == "READ" and not self.is_read:
            self.is_read = True
        elif self.is_read and self.read_status != "READ":
            self.read_status = "READ"
        return self


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    message: Optional[str] = None
    notification_type: Optional[str] = None
    read_status: Optional[str] = None
    is_read: Optional[bool] = None


class NotificationOut(BaseOut):
    notification_id: Optional[int | str] = None
    user_id: str
    message: str
    notification_type: Optional[str] = "INFO"
    read_status: Optional[str] = "UNREAD"
    is_read: bool = False
    sent_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 18. BATTERY_STATUS
# ---------------------------------------------------------------------------
class BatteryStatusBase(BaseModel):
    ev_id: str
    current_level: Optional[int] = Field(default=None, ge=0, le=100)
    battery_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    charging_level: Optional[int] = Field(default=0, ge=0, le=100)
    health_status: Optional[str] = "GOOD"
    temperature_c: Optional[float] = None
    last_updated: Optional[datetime] = None

    @model_validator(mode="after")
    def unify_battery_fields(self):
        if self.battery_percentage is None and self.current_level is not None:
            self.battery_percentage = float(self.current_level)
        elif self.current_level is None and self.battery_percentage is not None:
            self.current_level = int(self.battery_percentage)
        elif self.battery_percentage is None and self.current_level is None:
            self.battery_percentage = 80.0
            self.current_level = 80
        return self


class BatteryStatusCreate(BatteryStatusBase):
    pass


class BatteryStatusUpdate(BaseModel):
    current_level: Optional[int] = Field(default=None, ge=0, le=100)
    battery_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    charging_level: Optional[int] = Field(default=None, ge=0, le=100)
    health_status: Optional[str] = None
    temperature_c: Optional[float] = None
    last_updated: Optional[datetime] = None


class BatteryStatusOut(BaseOut):
    battery_status_id: Optional[int | str] = None
    ev_id: str
    current_level: int = 80
    battery_percentage: float = 80.0
    charging_level: int = 0
    health_status: Optional[str] = "GOOD"
    temperature_c: Optional[float] = None
    last_updated: Optional[datetime] = None
    recorded_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 19. RENEWABLE_SOURCE
# ---------------------------------------------------------------------------
class RenewableSourceBase(BaseModel):
    source_id: str
    renewable_type: str = "SOLAR"  # SOLAR, WIND, HYDRO, BIOMASS
    generation_efficiency: Optional[float] = Field(default=None, ge=0, le=100)
    name: Optional[str] = None
    source_type: str = "RENEWABLE"
    capacity_kw: Optional[float] = Field(default=1000.0, ge=0)
    energy_generated_kwh: float = 0.0
    status: str = "ACTIVE"


class RenewableSourceCreate(RenewableSourceBase):
    pass


class RenewableSourceUpdate(BaseModel):
    renewable_type: Optional[str] = None
    generation_efficiency: Optional[float] = Field(default=None, ge=0, le=100)
    name: Optional[str] = None
    capacity_kw: Optional[float] = Field(default=None, ge=0)
    energy_generated_kwh: Optional[float] = None
    status: Optional[str] = None


class RenewableSourceOut(BaseOut):
    source_id: str
    renewable_type: str = "SOLAR"
    generation_efficiency: Optional[float] = None
    name: Optional[str] = None
    source_type: str = "RENEWABLE"
    capacity_kw: float = 1000.0
    energy_generated_kwh: float = 0.0
    status: str = "ACTIVE"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 20. NON_RENEWABLE_SOURCE
# ---------------------------------------------------------------------------
class NonRenewableSourceBase(BaseModel):
    source_id: str
    fuel_type: str = "NATURAL_GAS"  # COAL, NATURAL_GAS, DIESEL, OIL
    emission_rate: Optional[float] = Field(default=None, ge=0)
    name: Optional[str] = None
    source_type: str = "NON_RENEWABLE"
    capacity_kw: Optional[float] = Field(default=2000.0, ge=0)
    energy_generated_kwh: float = 0.0
    status: str = "ACTIVE"


class NonRenewableSourceCreate(NonRenewableSourceBase):
    pass


class NonRenewableSourceUpdate(BaseModel):
    fuel_type: Optional[str] = None
    emission_rate: Optional[float] = Field(default=None, ge=0)
    name: Optional[str] = None
    capacity_kw: Optional[float] = Field(default=None, ge=0)
    energy_generated_kwh: Optional[float] = None
    status: Optional[str] = None


class NonRenewableSourceOut(BaseOut):
    source_id: str
    fuel_type: str = "NATURAL_GAS"
    emission_rate: Optional[float] = None
    name: Optional[str] = None
    source_type: str = "NON_RENEWABLE"
    capacity_kw: float = 2000.0
    energy_generated_kwh: float = 0.0
    status: str = "ACTIVE"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 21. PREVENTIVE_MAINTENANCE
# ---------------------------------------------------------------------------
class PreventiveMaintenanceBase(BaseModel):
    maintenance_id: str
    station_id: Optional[str] = None
    maintenance_interval: Optional[int] = Field(default=30, gt=0)  # days
    next_due_date: Optional[str] = None
    checklist: Optional[str] = None
    inspection_result: Optional[str] = "PASSED"
    title: Optional[str] = None
    description: Optional[str] = None
    status: str = "scheduled"


class PreventiveMaintenanceCreate(PreventiveMaintenanceBase):
    pass


class PreventiveMaintenanceUpdate(BaseModel):
    maintenance_interval: Optional[int] = Field(default=None, gt=0)
    next_due_date: Optional[str] = None
    checklist: Optional[str] = None
    inspection_result: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class PreventiveMaintenanceOut(BaseOut):
    maintenance_id: str
    station_id: Optional[str] = None
    maintenance_interval: Optional[int] = 30
    next_due_date: Optional[str] = None
    checklist: Optional[str] = None
    inspection_result: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: str = "scheduled"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 22. CORRECTIVE_MAINTENANCE
# ---------------------------------------------------------------------------
class CorrectiveMaintenanceBase(BaseModel):
    maintenance_id: str
    station_id: Optional[str] = None
    port_id: Optional[str] = None
    fault_description: Optional[str] = None
    fault_title: Optional[str] = None
    repair_action: Optional[str] = None
    severity: Optional[str] = "MEDIUM"
    repair_date: Optional[str] = None
    downtime: Optional[float] = Field(default=0.0, ge=0)
    resolution_status: Optional[str] = "PENDING"
    description: Optional[str] = None
    status: str = "open"
    reported_date: Optional[datetime] = None

    @model_validator(mode="after")
    def unify_corrective_fields(self):
        if not self.fault_title and self.fault_description:
            self.fault_title = (self.fault_description[:40] + "...") if len(self.fault_description) > 40 else self.fault_description
        elif not self.fault_description and self.fault_title:
            self.fault_description = self.fault_title
        return self


class CorrectiveMaintenanceCreate(CorrectiveMaintenanceBase):
    pass


class CorrectiveMaintenanceUpdate(BaseModel):
    fault_description: Optional[str] = None
    fault_title: Optional[str] = None
    repair_action: Optional[str] = None
    severity: Optional[str] = None
    repair_date: Optional[str] = None
    downtime: Optional[float] = Field(default=None, ge=0)
    resolution_status: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CorrectiveMaintenanceOut(BaseOut):
    maintenance_id: str
    station_id: Optional[str] = None
    port_id: Optional[str] = None
    fault_description: Optional[str] = None
    fault_title: Optional[str] = None
    repair_action: Optional[str] = None
    severity: Optional[str] = "MEDIUM"
    repair_date: Optional[str] = None
    downtime: Optional[float] = 0.0
    resolution_status: Optional[str] = "PENDING"
    description: Optional[str] = None
    status: str = "open"
    reported_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardStats(BaseModel):
    total_users: int
    total_stations: int
    total_ports: int
    total_bookings: int
    total_sessions: int
    total_revenue: float
    total_maintenance: int
    total_sources: Optional[int] = 0
    total_grids: Optional[int] = 0


class BookingTrend(BaseModel):
    date: str
    count: int


class RevenueTrend(BaseModel):
    date: str
    amount: float


class EnergyTrend(BaseModel):
    date: str
    kwh: float
