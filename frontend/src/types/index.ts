export type User = {
  id: string;
  user_id?: number | string | null;
  email: string;
  full_name: string;
  first_name?: string | null;
  last_name?: string | null;
  address?: string | null;
  date_of_birth?: string | null;
  role: "customer" | "admin";
  status: string;
  phone?: string | null;
  created_at: string;
};

export type Admin = {
  id: string;
  admin_id?: number | string | null;
  user_id?: string | null;
  email: string;
  admin_name?: string | null;
  full_name?: string | null;
  phone_no?: string | null;
  phone?: string | null;
  role: string;
  experience: number;
  privileges: string[];
  status?: string;
  created_at?: string;
};

export type EV = {
  id: string;
  ev_id?: number | string | null;
  owner_id?: string;
  user_id?: string;
  model: string;
  brand?: string | null;
  manufacturer?: string | null;
  registration_number: string;
  vehicle_number?: string | null;
  battery_capacity_kwh: number;
  battery_capacity?: number;
  connector_type: string;
  manufacturing_year?: number | null;
  manufacture_year?: number | null;
  is_active: boolean;
  status?: string;
  created_at: string;
};

export type UserPhone = {
  id: string;
  user_id: string;
  number: string;
  phone_no?: string;
  label?: string | null;
  phone_type?: string | null;
  is_primary: boolean;
  created_at?: string;
};

export type Station = {
  id: string;
  station_id?: number | string | null;
  name: string;
  station_name?: string;
  station_code: string;
  address: string;
  city?: string;
  latitude: number;
  longitude: number;
  operating_hours?: string;
  grid_id?: string | null;
  status: string;
  total_ports?: number;
  created_at: string;
};

export type Port = {
  id: string;
  port_id?: number | string | null;
  station_id: string;
  station_code?: string;
  port_number: number;
  charger_type?: string;
  connector_type: string;
  rated_power_kw: number;
  power_output?: number;
  availability_status?: string;
  status: string;
  tariff_id?: string | null;
  created_at: string;
};

export type ACPort = {
  id: string;
  port_id?: string;
  station_id: string;
  port_number: number;
  connector_standard: string;
  ac_phase: string;
  ac_power_kw?: number;
  voltage?: number;
  current?: number;
  created_at?: string;
};

export type DCFastPort = {
  id: string;
  port_id?: string;
  station_id: string;
  port_number: number;
  dc_voltage: number;
  maximum_current: number;
  dc_power_kw?: number;
  supported_standard?: string;
  created_at?: string;
};

export type Tariff = {
  id: string;
  tariff_id?: number | string | null;
  name: string;
  tariff_name?: string;
  price_per_kwh: number;
  rate_per_kwh?: number;
  peak_hour_rate?: number;
  off_peak_rate?: number;
  valid_from: string;
  start_date?: string;
  valid_to?: string | null;
  end_date?: string | null;
  description?: string | null;
  is_active: boolean;
  status?: string;
  created_at: string;
};

export type Source = {
  id: string;
  source_id?: number | string | null;
  name: string;
  source_name?: string;
  source_type: string;
  capacity_kw: number;
  capacity?: number;
  unit?: string;
  status: string;
  energy_generated_kwh: number;
  description?: string | null;
  created_at?: string;
};

export type RenewableSource = {
  id: string;
  source_id: string;
  renewable_type: string;
  generation_efficiency?: number;
  name?: string;
  source_type: string;
  capacity_kw: number;
  energy_generated_kwh: number;
  status: string;
  created_at?: string;
};

export type NonRenewableSource = {
  id: string;
  source_id: string;
  fuel_type: string;
  emission_rate?: number;
  name?: string;
  source_type: string;
  capacity_kw: number;
  energy_generated_kwh: number;
  status: string;
  created_at?: string;
};

export type Grid = {
  id: string;
  grid_id?: number | string | null;
  name: string;
  grid_name?: string;
  voltage_level?: string;
  capacity_kw: number;
  capacity?: number;
  current_load_kw: number;
  current_load?: number;
  location?: string | null;
  status: string;
  source_id?: string | null;
  created_at?: string;
};

export type Booking = {
  id: string;
  booking_id?: number | string | null;
  user_id: string;
  ev_id: string;
  station_id: string;
  port_id: string;
  port_number?: number;
  booking_date?: string;
  booking_time?: string;
  start_time: string;
  end_time: string;
  status: string;
  booking_status?: string;
  created_at: string;
};

export type Session = {
  id: string;
  session_id?: number | string | null;
  booking_id?: string | null;
  user_id: string;
  ev_id?: string | null;
  port_id: string;
  started_at: string;
  start_time?: string;
  ended_at?: string | null;
  end_time?: string | null;
  energy_delivered_kwh?: number | null;
  energy_consumed_kwh?: number | null;
  energy_consumed?: number | null;
  total_amount?: number | null;
  tariff_price_per_kwh?: number | null;
  status: string;
  session_status?: string;
};

export type Payment = {
  id: string;
  payment_id?: number | string | null;
  session_id: string;
  user_id: string;
  amount: number;
  payment_method: string;
  payment_mode?: string;
  payment_date?: string;
  transaction_reference: string;
  status: string;
  payment_status?: string;
  created_at: string;
};

export type Schedule = {
  id: string;
  schedule_id?: number | string | null;
  station_id: string;
  port_id?: string | null;
  schedule_date?: string;
  start_time: string;
  end_time: string;
  available_slots: number;
  schedule_type?: string;
  is_available: boolean;
  status?: string;
  description?: string | null;
  note?: string | null;
  created_at?: string;
};

export type Maintenance = {
  id: string;
  maintenance_id?: number | string | null;
  station_id?: string | null;
  port_id?: string | null;
  admin_id?: string | null;
  maintenance_type: string;
  title?: string | null;
  description?: string | null;
  scheduled_date?: string | null;
  maintenance_date?: string | null;
  completion_date?: string | null;
  cost: number;
  status: string;
  created_at: string;
};

export type PreventiveMaintenance = {
  id: string;
  maintenance_id: string;
  station_id?: string | null;
  maintenance_interval?: number;
  next_due_date?: string | null;
  checklist?: string | null;
  inspection_result?: string | null;
  title?: string | null;
  description?: string | null;
  status: string;
  created_at?: string;
};

export type CorrectiveMaintenance = {
  id: string;
  maintenance_id: string;
  station_id?: string | null;
  port_id?: string | null;
  fault_title?: string | null;
  fault_description?: string | null;
  repair_action?: string | null;
  severity?: string;
  repair_date?: string | null;
  downtime?: number;
  resolution_status?: string;
  description?: string | null;
  status: string;
  reported_date?: string | null;
  created_at?: string;
};

export type Notification = {
  id: string;
  notification_id?: number | string | null;
  user_id: string;
  message: string;
  notification_type?: string;
  read_status?: string;
  is_read: boolean;
  sent_date?: string;
  created_at: string;
};

export type BatteryStatus = {
  id: string;
  battery_status_id?: number | string | null;
  ev_id: string;
  current_level: number;
  battery_percentage: number;
  charging_level: number;
  health_status?: string;
  temperature_c?: number | null;
  last_updated?: string;
  recorded_at?: string;
};

export type DashboardStats = {
  total_users: number;
  total_stations: number;
  total_ports: number;
  total_bookings: number;
  total_sessions: number;
  total_revenue: number;
  total_maintenance: number;
  total_sources?: number;
  total_grids?: number;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};
