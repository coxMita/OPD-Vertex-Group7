export type ConsultationPatient = {
  id: string
  name: string
  time: string
  department: string
  status: 'waiting' | 'active' | 'done'
  tag: 'new' | 'follow-up' | 'urgent'
  phone: string
  email: string
  dob: string
  age: number
  gender: string
  cpr: string
  blood: string
  allergy: string
  reason: string
}

export type RxDraft = {
  text: string
}

export function useConsultationData() {
  const appointment: ConsultationPatient = {
    id: 'appt-001',
    name: 'Maria Andersen',
    time: '09:00',
    department: 'General Practice',
    status: 'waiting',
    tag: 'new',
    phone: '+45 28 44 61 02',
    email: 'm.andersen@gmail.com',
    dob: '14 Mar 1988',
    age: 37,
    gender: 'Female',
    cpr: '1403882941',
    blood: 'A+',
    allergy: 'Penicillin',
    reason: 'Sore throat and mild fever for 3 days',
  }

  const rxDraft: RxDraft = {
    text: `PATIENT: Maria Andersen
DATE: ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}  |  DR. HANSEN

MEDICATIONS:
1. Amoxicillin 500mg — 3× daily for 7 days
   Take with food. Complete full course.
2. Ibuprofen 400mg — as needed (max 3/day)
   Avoid on empty stomach.

NOTES:
Follow-up in 1 week if symptoms persist.
Avoid dairy 2h before/after Amoxicillin.`,
  }

  return { appointment, rxDraft }
}