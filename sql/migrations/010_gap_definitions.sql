ALTER TABLE `question_choice_recommendations`
  ADD COLUMN `gap_definition` text NULL AFTER `severity`;

ALTER TABLE `gap_flags`
  ADD COLUMN `gap_definition` text NULL AFTER `description`;
