INSERT INTO "tblIncomeLevels" ("FirstLanguage", "SecondLanguage") VALUES
('Néant', 'Nothing'),
('<30 000', '<30 000'),
('30 000-40 000', '30 000-40 000'),
('40 000-50 000', '40 000-50 000'),
('50 000-60 000', '50 000-60 000'),
('60 000-75 000', '60 000-75 000'),
('75 000-200 000', '75 000-200 000'),
('200 000-300 000', '200 000-300 000'),
('300 000-600 000', '300 000-600 000'),
('>600 000', '>600 000');


INSERT INTO public."tblResidenceEnvironment" ("Code", "ResidenceEnvironment", "AltLanguage", "SortOrder")
VALUES
    (1, 'Urban', 'Urbain', 1),
    (2, 'Rural', 'Rural', 2);

INSERT INTO public."tblNoDisability" ("Code", "NoDisabilityLabel", "AltLanguage", "SortOrder")
VALUES
    (1, 'Without disability', 'Sans handicap', 1),
    (2, 'With disability', 'Avec handicap', 2);


INSERT INTO public."tblNonDisablingDisease" ("Code", "NonDisablingDisease", "AltLanguage", "SortOrder")
VALUES
    (1, 'Without disabling disease', 'Sans maladie invalidante', 1),
    (2, 'With disabling disease', 'Avec maladie invalidante', 2);

INSERT INTO public."tblMutualInsuranceCoverage" ("Code", "MutualInsuranceCoverage", "AltLanguage", "SortOrder")
VALUES
    (1, 'Without health insurance or mutual coverage', 'Sans couverture en assurance maladie', 1),
    (2, 'With health insurance or mutual coverage', 'Avec une couverture en assurance maladie ou mutuelle de santé', 2);

INSERT INTO public."tblHousingType" ("Code", "HousingType", "AltLanguage", "SortOrder")
VALUES
    (1, 'Villa', 'Villa', 1),
    (2, 'Hard building with floor', 'En dur et à étage', 2),
    (3, 'Hard building (cement, baked bricks, etc.)', 'En dur (ciment, brique cuite, …)', 3),
    (4, 'Sheet metal, tiled floor, sheet metal roof', 'En tôle, sol en carrelage, toit en tôle', 4),
    (5, 'Sheet metal, tiled floor, straw roof', 'En tôle, sol en carrelage, toit en paille', 5),
    (6, 'Sheet metal, cement floor, sheet metal roof', 'En tôle, sol en ciment, toit en tôle', 6),
    (7, 'Sheet metal, cement floor, straw roof', 'En tôle, sol en ciment, toit en paille', 7),
    (8, 'Sheet metal, dirt floor, sheet metal roof', 'En tôle, sol en terre, toit en tôle', 8),
    (9, 'Sheet metal, dirt floor, straw roof', 'En tôle, sol en terre, toit en paille', 9),
    (11, 'Mud, tiled floor, straw roof', 'En terre battue, sol en carrelage, toit en paille', 11),
    (12, 'Mud, cement floor, sheet metal roof', 'En terre battue, sol en ciment, toit en tôle', 12),
    (13, 'Mud, cement floor, straw roof', 'En terre battue, sol en ciment, toit en paille', 13),
    (15, 'Mud, dirt floor, straw roof', 'En terre battue, sol en terre, toit en paille', 15),
    (16, 'Straw, tiled floor, sheet metal roof', 'En paille, sol en carrelage, toit en tôle', 16),
    (17, 'Straw, tiled floor, straw roof', 'En paille, sol en carrelage, toit en paille', 17),
    (18, 'Straw, cement floor, sheet metal roof', 'En paille, sol en ciment, toit en tôle', 18),
    (19, 'Straw, cement floor, straw roof', 'En paille, sol en ciment, toit en paille', 19),
    (20, 'Straw, dirt floor, sheet metal roof', 'En paille, sol en terre, toit en tôle', 20),
    (21, 'Straw, dirt floor, straw roof', 'En paille, sol en terre, toit en paille', 21);
