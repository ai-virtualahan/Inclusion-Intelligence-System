UPDATE question_choice_recommendations qcr
JOIN question_choices qc
  ON qcr.choice_id = qc.id
JOIN question_bank qb
  ON qc.question_id = qb.id
SET qcr.recommendation_text = CONCAT(
  CASE
    WHEN qc.choice_score <= 1 THEN 'Critical action: '
    WHEN qc.choice_score <= 2 THEN 'Moderate action: '
    ELSE 'Optional improvement: '
  END,
  CASE
    WHEN qc.choice_score <= 1 THEN 'start immediately and assign an owner to '
    WHEN qc.choice_score <= 2 THEN 'formalize the plan, timeline, and accountability to '
    ELSE 'strengthen documentation and monitoring to '
  END,
  CASE COALESCE(qb.version_group_id, qb.id)
    WHEN 1 THEN 'update all job postings to explicitly welcome candidates with disabilities and list available accommodations.'
    WHEN 2 THEN 'complete an accessibility review of the online application process and provide alternative application formats.'
    WHEN 3 THEN 'standardize disability-aware candidate screening with structured rubrics and bias controls.'
    WHEN 4 THEN 'make interview accommodations proactive, documented, and consistent across hiring teams.'
    WHEN 5 THEN 'review selection criteria so only essential job requirements are used in hiring decisions.'
    WHEN 6 THEN 'set measurable PWD hiring targets and review progress with leadership on a regular schedule.'
    WHEN 7 THEN 'build active sourcing partnerships with disability-focused organizations, job boards, and communities.'
    WHEN 8 THEN 'review pre-employment tests and tasks for accessibility before candidates are asked to complete them.'
    WHEN 9 THEN 'include accommodation needs, flexible start options, and agreed support in the offer-stage process.'
    WHEN 10 THEN 'collect and analyze disability-related hiring data across the recruitment pipeline.'
    WHEN 11 THEN 'create a pre-boarding checklist for PWD new hires covering workspace, tools, access needs, and support contacts.'
    WHEN 12 THEN 'convert orientation and onboarding materials into accessible, screen-reader-ready, and captioned formats.'
    WHEN 13 THEN 'assign trained buddies or mentors and schedule structured check-ins during the onboarding period.'
    WHEN 14 THEN 'define accommodation response timelines and a clear owner for requests raised during onboarding.'
    WHEN 15 THEN 'train managers before onboarding employees with disabilities and document completion.'
    WHEN 16 THEN 'use written 30-60-90 day plans that account for role expectations and any needed adjustments.'
    WHEN 17 THEN 'provide personalized physical workplace orientation, including accessible routes and emergency procedures.'
    WHEN 18 THEN 'confirm digital tools and accessibility settings are ready before the employee starts.'
    WHEN 19 THEN 'use an inclusive team introduction protocol agreed with the new hire in advance.'
    WHEN 20 THEN 'schedule onboarding experience check-ins and document follow-up actions for PWD new hires.'
    WHEN 21 THEN 'publish and communicate a written accommodation policy that is easy for employees to access.'
    WHEN 22 THEN 'document the accommodation request process with clear steps, contacts, and expected timelines.'
    WHEN 23 THEN 'track accommodation response times and set service-level expectations for resolution.'
    WHEN 24 THEN 'train managers on receiving, documenting, and acting on accommodation requests without bias.'
    WHEN 25 THEN 'assess physical accessibility gaps and maintain a remediation plan for office spaces.'
    WHEN 26 THEN 'audit core digital tools against accessibility standards and prioritize remediation.'
    WHEN 27 THEN 'create a clear assistive technology request, approval, procurement, and setup process.'
    WHEN 28 THEN 'recognize flexible and remote work as formal accommodation options where role-compatible.'
    WHEN 29 THEN 'document confidentiality protocols for disability disclosure and accommodation requests.'
    WHEN 30 THEN 'review accommodations periodically with employees and update support as roles or needs change.'
    WHEN 31 THEN 'track PWD attrition against overall attrition and investigate gaps through a retention action plan.'
    WHEN 32 THEN 'monitor PWD participation in career development and remove barriers to equitable access.'
    WHEN 33 THEN 'analyze promotion equity for PWD employees and remediate any disparities found.'
    WHEN 34 THEN 'review performance management for disability-related bias and train managers on equitable evaluation.'
    WHEN 35 THEN 'make mentoring and sponsorship programs accessible and actively recruit PWD participants.'
    WHEN 36 THEN 'capture disability-related trends in exit interviews and use findings for retention interventions.'
    WHEN 37 THEN 'create a structured return-to-work process with accommodation review and manager guidance.'
    WHEN 38 THEN 'measure psychological safety for PWD employees and respond to concerns through accountable action plans.'
    WHEN 39 THEN 'review team events and social activities for accessibility before scheduling.'
    WHEN 40 THEN 'assign executive ownership and metrics for long-term PWD retention.'
    WHEN 41 THEN 'make senior leadership commitment to disability inclusion visible through regular actions and communications.'
    WHEN 42 THEN 'create or strengthen a disability-specific inclusion policy with named accountability.'
    WHEN 43 THEN 'publish an inclusive language guide and train managers to address non-inclusive language.'
    WHEN 44 THEN 'roll out recurring disability awareness training and track completion.'
    WHEN 45 THEN 'establish or strengthen a PWD employee resource group with sponsorship, budget, and programming.'
    WHEN 46 THEN 'plan and resource disability awareness programming with measurable outcomes.'
    WHEN 47 THEN 'collect PWD-specific culture feedback and convert findings into tracked action plans.'
    WHEN 48 THEN 'extend disability inclusion standards into supplier and partner selection or engagement practices.'
    WHEN 49 THEN 'recognize PWD employee contributions with consent and include disability inclusion in recognition programs.'
    WHEN 50 THEN 'measure disability inclusion culture using a structured tool and maintain an annual improvement plan.'
    ELSE 'address the gap identified by the selected answer.'
  END
)
WHERE qc.choice_score <= 3;

UPDATE gap_flags gf
JOIN question_choice_recommendations qcr
  ON qcr.choice_id = gf.selected_choice_id
  AND qcr.severity = gf.severity
SET gf.recommendation_text = qcr.recommendation_text
WHERE gf.selected_choice_id IS NOT NULL
  AND gf.id > 0;
