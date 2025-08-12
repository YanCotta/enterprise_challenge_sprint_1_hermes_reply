--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: alert_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.alert_status AS ENUM (
    'open',
    'acknowledged',
    'resolved',
    'ignored'
);


--
-- Name: maintenancetaskstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.maintenancetaskstatus AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'PARTIALLY_COMPLETED',
    'FAILED',
    'CANCELLED'
);


--
-- Name: sensor_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sensor_status AS ENUM (
    'active',
    'inactive',
    'maintenance',
    'decommissioned'
);


--
-- Name: task_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.task_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _compressed_hypertable_2; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._compressed_hypertable_2 (
);


--
-- Name: sensor_readings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sensor_readings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sensor_readings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings (
    id integer DEFAULT nextval('public.sensor_readings_id_seq'::regclass) NOT NULL,
    sensor_id character varying(255) NOT NULL,
    sensor_type character varying(50) NOT NULL,
    value double precision NOT NULL,
    unit character varying(50),
    "timestamp" timestamp with time zone NOT NULL,
    quality double precision,
    sensor_metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: _hyper_1_2_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_1_2_chunk (
    CONSTRAINT constraint_2 CHECK ((("timestamp" >= '2025-08-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-08-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.sensor_readings);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: anomaly_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_alerts (
    id uuid NOT NULL,
    sensor_id character varying(255) NOT NULL,
    anomaly_type character varying(100) NOT NULL,
    severity integer NOT NULL,
    confidence double precision,
    description text,
    evidence jsonb,
    recommended_actions character varying[],
    status public.alert_status NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: maintenance_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_logs (
    id uuid NOT NULL,
    task_id uuid NOT NULL,
    equipment_id character varying(255) NOT NULL,
    completion_date timestamp with time zone NOT NULL,
    technician_id character varying(255) NOT NULL,
    notes text,
    status public.maintenancetaskstatus NOT NULL,
    actual_duration_hours double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: maintenance_tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_tasks (
    id uuid NOT NULL,
    equipment_id character varying(255) NOT NULL,
    task_type character varying(100) NOT NULL,
    description text,
    priority integer NOT NULL,
    status public.task_status NOT NULL,
    estimated_duration_hours double precision,
    actual_duration_hours double precision,
    required_skills character varying[],
    parts_needed character varying[],
    assigned_technician_id character varying(255),
    scheduled_start_time timestamp with time zone,
    scheduled_end_time timestamp with time zone,
    actual_start_time timestamp with time zone,
    actual_end_time timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    sensor_id character varying(255)
);


--
-- Name: sensors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensors (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    sensor_id character varying(255) NOT NULL,
    type character varying(50) NOT NULL,
    location character varying(255),
    status public.sensor_status DEFAULT 'active'::public.sensor_status NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: _hyper_1_2_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_2_chunk ALTER COLUMN id SET DEFAULT nextval('public.sensor_readings_id_seq'::regclass);


--
-- Name: _hyper_1_2_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_2_chunk ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;


--
-- Name: _hyper_1_2_chunk updated_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_2_chunk ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;


--
-- Name: _hyper_1_2_chunk 2_4_sensor_readings_pkey; Type: CONSTRAINT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_2_chunk
    ADD CONSTRAINT "2_4_sensor_readings_pkey" PRIMARY KEY ("timestamp", sensor_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: anomaly_alerts anomaly_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_alerts
    ADD CONSTRAINT anomaly_alerts_pkey PRIMARY KEY (id);


--
-- Name: maintenance_logs maintenance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_logs
    ADD CONSTRAINT maintenance_logs_pkey PRIMARY KEY (id);


--
-- Name: maintenance_tasks maintenance_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_pkey PRIMARY KEY (id);


--
-- Name: sensor_readings sensor_readings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings
    ADD CONSTRAINT sensor_readings_pkey PRIMARY KEY ("timestamp", sensor_id);


--
-- Name: sensors sensors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_pkey PRIMARY KEY (id);


--
-- Name: sensors uq_sensors_sensor_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT uq_sensors_sensor_id UNIQUE (sensor_id);


--
-- Name: _hyper_1_2_chunk_ix_sensor_readings_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_2_chunk_ix_sensor_readings_id ON _timescaledb_internal._hyper_1_2_chunk USING btree (id);


--
-- Name: _hyper_1_2_chunk_ix_sensor_readings_sensor_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_2_chunk_ix_sensor_readings_sensor_id ON _timescaledb_internal._hyper_1_2_chunk USING btree (sensor_id);


--
-- Name: _hyper_1_2_chunk_ix_sensor_readings_timestamp; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_2_chunk_ix_sensor_readings_timestamp ON _timescaledb_internal._hyper_1_2_chunk USING btree ("timestamp");


--
-- Name: ix_anomaly_alerts_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_alerts_id ON public.anomaly_alerts USING btree (id);


--
-- Name: ix_anomaly_alerts_sensor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_alerts_sensor_id ON public.anomaly_alerts USING btree (sensor_id);


--
-- Name: ix_maintenance_logs_equipment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenance_logs_equipment_id ON public.maintenance_logs USING btree (equipment_id);


--
-- Name: ix_maintenance_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenance_logs_id ON public.maintenance_logs USING btree (id);


--
-- Name: ix_maintenance_logs_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenance_logs_task_id ON public.maintenance_logs USING btree (task_id);


--
-- Name: ix_maintenance_tasks_equipment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenance_tasks_equipment_id ON public.maintenance_tasks USING btree (equipment_id);


--
-- Name: ix_maintenance_tasks_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenance_tasks_id ON public.maintenance_tasks USING btree (id);


--
-- Name: ix_maintenance_tasks_sensor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenance_tasks_sensor_id ON public.maintenance_tasks USING btree (sensor_id);


--
-- Name: ix_sensor_readings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sensor_readings_id ON public.sensor_readings USING btree (id);


--
-- Name: ix_sensor_readings_sensor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sensor_readings_sensor_id ON public.sensor_readings USING btree (sensor_id);


--
-- Name: ix_sensor_readings_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sensor_readings_timestamp ON public.sensor_readings USING btree ("timestamp");


--
-- Name: _compressed_hypertable_2 ts_insert_blocker; Type: TRIGGER; Schema: _timescaledb_internal; Owner: -
--

CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON _timescaledb_internal._compressed_hypertable_2 FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();


--
-- Name: sensor_readings ts_insert_blocker; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.sensor_readings FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();


--
-- Name: _hyper_1_2_chunk 2_3_fk_sensor_readings_sensor; Type: FK CONSTRAINT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_2_chunk
    ADD CONSTRAINT "2_3_fk_sensor_readings_sensor" FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id) ON DELETE RESTRICT;


--
-- Name: anomaly_alerts fk_anomaly_alerts_sensor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_alerts
    ADD CONSTRAINT fk_anomaly_alerts_sensor FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id) ON DELETE RESTRICT;


--
-- Name: maintenance_tasks fk_maintenance_tasks_sensor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT fk_maintenance_tasks_sensor FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id) ON DELETE RESTRICT;


--
-- Name: sensor_readings fk_sensor_readings_sensor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings
    ADD CONSTRAINT fk_sensor_readings_sensor FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

