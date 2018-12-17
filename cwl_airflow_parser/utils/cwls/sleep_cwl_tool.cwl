class: CommandLineTool
cwlVersion: v1.0


hints:
  - class: DockerRequirement
    dockerPull: ubuntu:xenial


inputs:

  delay:
    type: int?
    inputBinding:
      position: 1
    default: 5


outputs:

  empty_file:
    type: File?
    outputBinding:
      glob: "*"


baseCommand: [sleep]