// src/services/userApi.ts
import { authClient, publicClient } from './httpClient'

export interface DoctorResponse {
  doctor_id: string
  full_name: string
  department_name: string
  email: string
  keycloak_id: string
}

export interface PatientResponse {
  patient_id: string
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  phone_number: number
  email: string
}

export interface PatientFindOrCreateRequest {
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  phone_number: number
  email: string
}

export const userApi = {
  // ── PUBLIC (pacient) ──────────────────────────────────────────
  getDoctorsByDepartment(departmentName: string): Promise<DoctorResponse[]> {
    return publicClient
      .get<DoctorResponse[]>(
        `/api/v1/user/doctor/${encodeURIComponent(departmentName)}/doctors`,
      )
      .then((res) => res.data)
  },

  lookupPatientByEmail(email: string): Promise<PatientResponse> {
    return publicClient
      .get<PatientResponse>('/api/v1/user/patients/by-email', {
        params: { email },
      })
      .then((res) => res.data)
  },

  findOrCreatePatient(data: PatientFindOrCreateRequest): Promise<PatientResponse> {
    return publicClient
      .post<PatientResponse>('/api/v1/user/patients', data)
      .then((res) => res.data)
  },

  // ── PROTECTED (doctor) ────────────────────────────────────────
  getDoctor(doctorId: string): Promise<DoctorResponse> {
    return authClient
      .get<DoctorResponse>(`/api/v1/user/doctors/${doctorId}`)
      .then((res) => res.data)
  },

  getPatient(patientId: string): Promise<PatientResponse> {
    return authClient
      .get<PatientResponse>(`/api/v1/user/patients/${patientId}`)
      .then((res) => res.data)
  },

  getDoctorByKeycloakId(keycloakId: string): Promise<DoctorResponse> {
    return authClient
      .get<DoctorResponse>('/api/v1/user/doctors/me', {
        params: { keycloak_id: keycloakId },
      })
      .then((res) => res.data)
  },
}