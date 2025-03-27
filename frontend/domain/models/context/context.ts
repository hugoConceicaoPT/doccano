export class Context {
    constructor(readonly id: number, readonly text: string, readonly exampleId: string | number) {}
  
    static create(text: string, exampleId: string | number): Context {
      return new Context(0, text, exampleId)
    }
  }
  