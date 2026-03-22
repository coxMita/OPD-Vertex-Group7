import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

export interface DoctorResponse {
  id: string
  first_name: string
  last_name: string
  specialization: string
  keycloak_id: string | null
}

export interface PatientResponse {
  id: string
  first_name: string
  last_name: string
  email: string
  phone: string | null
  date_of_birth: string | null
  gender: string | null
}

export interface PatientFindOrCreateRequest {
  first_name: string
  last_name: string
  email: string
  phone?: string
  date_of_birth: string   // "YYYY-MM-DD"
  gender: string          // "male" | "female" | "other"
}

export const userApi = {
  /**
   * Fetch all doctors.
   * Maps to: GET /api/v1/users/doctors
   */
  getAllDoctors(): Promise<DoctorResponse[]> {
    return apiClient
      .get<DoctorResponse[]>('/api/v1/users/doctors')
      .then((res) => res.data)
  },

  /**
   * Fetch a single doctor by ID.
   * Maps to: GET /api/v1/users/doctors/{id}
   */
  getDoctor(doctorId: string): Promise<DoctorResponse> {
    return apiClient
      .get<DoctorResponse>(`/api/v1/users/doctors/${doctorId}`)
      .then((res) => res.data)
  },

    lookupPatientByEmail(email: string): Promise<PatientResponse> {
    return apiClient
        .get<PatientResponse>('/api/v1/users/patients/lookup', {
        params: { email },
        })
        .then((res) => res.data)
    },

  /**
   * Find or create a patient by email.
   * Maps to: POST /api/v1/users/patients
   */
  findOrCreatePatient(data: PatientFindOrCreateRequest): Promise<PatientResponse> {
    return apiClient
      .post<PatientResponse>('/api/v1/users/patients', data)
      .then((res) => res.data)
  },

  /**
   * Fetch a single patient by ID.
   * Maps to: GET /api/v1/users/patients/{id}
   */
  getPatient(patientId: string): Promise<PatientResponse> {
    return apiClient
      .get<PatientResponse>(`/api/v1/users/patients/${patientId}`)
      .then((res) => res.data)
  },
}