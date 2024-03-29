// https://docs.renovatebot.com/self-hosted-configuration/

module.exports = {
  username: 'renovate-release',
  platform: 'github',
  baseBranches: ['main'],
  onboarding: true,
  dryRun: 'lookup',
  rangeStrategy: 'pin',
  packageRules: [
    {
      automerge: true,
      matchUpdateTypes: [
        'pin',
        'digest',
        'patch',
        'minor',
        'major',
        'lockFileMaintenance',
      ],
      matchDepTypes: ["devDependencies"],
      dependencyDashboardApproval: false,
      minimumReleaseAge: 0,
    },
  ],
};
