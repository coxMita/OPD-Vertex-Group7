import apiClient from './apiClient'

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
  date_of_birth: string   // "YYYY-MM-DD"
  gender: string
  phone_number: number
  email: string
}

export interface PatientFindOrCreateRequest {
  first_name: string
  last_name: string
  date_of_birth: string   // "YYYY-MM-DD"
  gender: string
  phone_number: number
  email: string
}

export const userApi = {
  /**
   * Fetch all doctors in a department.
   * Maps to: GET /api/v1/user/doctor/{department_name}/doctors
   */
  getDoctorsByDepartment(departmentName: string): Promise<DoctorResponse[]> {
    return apiClient
      .get<DoctorResponse[]>(`/api/v1/user/doctor/${encodeURIComponent(departmentName)}/doctors`)
      .then((res) => res.data)
  },

  lookupPatientByEmail(email: string): Promise<PatientResponse> {
  return apiClient
    .get<PatientResponse>('/api/v1/user/patients/by-email', {
      params: { email },
    })
    .then((res) => res.data)
},

  /**
   * Fetch a single doctor by ID.
   * Maps to: GET /api/v1/user/doctors/{doctor_id}
   */
  getDoctor(doctorId: string): Promise<DoctorResponse> {
    return apiClient
      .get<DoctorResponse>(`/api/v1/user/doctors/${doctorId}`)
      .then((res) => res.data)
  },

  /**
   * Find or create a patient.
   * Maps to: POST /api/v1/user/patients
   */
  findOrCreatePatient(data: PatientFindOrCreateRequest): Promise<PatientResponse> {
    return apiClient
      .post<PatientResponse>('/api/v1/user/patients', data)
      .then((res) => res.data)
  },

  /**
   * Fetch a single patient by ID.
   * Maps to: GET /api/v1/user/patients/{patient_id}
   */
  getPatient(patientId: string): Promise<PatientResponse> {
    return apiClient
      .get<PatientResponse>(`/api/v1/user/patients/${patientId}`)
      .then((res) => res.data)
  },
}