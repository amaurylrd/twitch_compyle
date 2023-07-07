module.exports = {
    endpoint: 'https://self-hosted.gitlab/api/v4/',
    token: '**gitlab_token**',
    platform: 'gitlab',
    onboardingConfig: {
      extends: ['config:base'],
    },
    repositories: ['username/repo', 'orgname/repo'],
  };